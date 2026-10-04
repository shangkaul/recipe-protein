import json
import os
import re
import sqlite3
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from .pantry import normalize
from .safety import contains_red_meat


DEFAULT_DB_PATH = Path(__file__).parents[2] / "data" / "recipe1m.sqlite"
DEFAULT_IMAGE_CACHE = Path(__file__).parents[2] / "data" / "recipe1m-images"
QUERY_TOKEN_RE = re.compile(r"[a-z0-9]+")
QUERY_STOPWORDS = {"and", "or", "the", "with", "some", "my", "a", "an", "of"}
SCHEMA_VERSION = "2"
# A single human serving cannot hold more than this. Values beyond it mean the recipe's yield or
# the confirmed serving count is wrong, so no per-serving figure is returned.
MAX_SERVING_PROTEIN_G = 150
MAX_SERVING_CALORIES = 1_500
MAX_CONFIRMED_SERVINGS = 24
LOCAL_PANTRY_TERMS = {
    "pasta", "spaghetti", "penne", "macaroni", "linguine", "fettuccine", "rigatoni",
    "tagliatelle", "vermicelli", "noodles", "ramen", "soba", "udon",
}


class Recipe1MIndex:
    """Read-only adapter for the optional, local Recipe1M SQLite index."""

    def __init__(self, path: str | Path | None = None, image_cache: str | Path | None = None):
        configured_path = path or os.getenv("RECIPE1M_DB_PATH") or DEFAULT_DB_PATH
        configured_cache = image_cache or os.getenv("RECIPE1M_IMAGE_CACHE") or DEFAULT_IMAGE_CACHE
        self.path = Path(configured_path).expanduser()
        self.image_cache = Path(configured_cache).expanduser()

    @property
    def available(self) -> bool:
        if not self.path.is_file():
            return False
        try:
            with self._connect() as connection:
                complete = connection.execute(
                    "SELECT 1 FROM metadata WHERE key = 'complete' AND value = '1'"
                ).fetchone() is not None
                schema = connection.execute(
                    "SELECT value FROM metadata WHERE key = 'schema_version'"
                ).fetchone()
                return complete and schema is not None and schema[0] == SCHEMA_VERSION
        except sqlite3.Error:
            return False

    @property
    def known_terms(self) -> set[str]:
        return LOCAL_PANTRY_TERMS if self.available else set()

    def status(self) -> dict:
        result = {"available": self.available, "path": str(self.path), "recipes": 0}
        if result["available"]:
            with self._connect() as connection:
                row = connection.execute("SELECT value FROM metadata WHERE key = 'safe_recipes'").fetchone()
                result["recipes"] = int(row[0]) if row else 0
        return result

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, timeout=2)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection

    def search(
        self,
        terms: list[str],
        exclusions: set[str],
        limit: int = 160,
        verified_nutrition_only: bool = False,
    ) -> list[dict]:
        if not self.available:
            return []
        query = self._fts_query(terms)
        if not query:
            return []
        nutrition_clause = ""
        if verified_nutrition_only:
            # Mirror minimum_servings in SQL so the filter only offers recipes the user can
            # actually divide into a plausible portion.
            nutrition_clause = (
                "AND recipes.protein_total IS NOT NULL"
                f" AND recipes.protein_total <= {MAX_SERVING_PROTEIN_G * MAX_CONFIRMED_SERVINGS}"
                f" AND recipes.calories_total <= {MAX_SERVING_CALORIES * MAX_CONFIRMED_SERVINGS}"
            )
        sql = f"""
            SELECT recipes.*, -bm25(recipe_fts, 0.0, 8.0, 5.0, 1.0) AS lexical_score
            FROM recipe_fts
            JOIN recipes ON recipes.rowid = recipe_fts.rowid
            WHERE recipe_fts MATCH ?
            {nutrition_clause}
            ORDER BY bm25(recipe_fts, 0.0, 8.0, 5.0, 1.0)
            LIMIT ?
        """
        try:
            with self._connect() as connection:
                rows = connection.execute(sql, (query, limit)).fetchall()
        except sqlite3.Error:
            return []

        candidates = []
        for row in rows:
            ingredients = json.loads(row["ingredients_json"])
            searchable = [normalize(item) for item in ingredients]
            if contains_red_meat(" ".join([row["title"], *ingredients])):
                continue
            if exclusions and any(
                any(_phrase_matches(term, ingredient) for ingredient in searchable)
                for term in exclusions
            ):
                continue
            candidates.append(self._record(row, ingredients))
        return candidates

    def detail(self, slug: str) -> dict | None:
        recipe_id = self.recipe_id(slug)
        if not recipe_id or not self.available:
            return None
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM recipes WHERE recipe_id = ?", (recipe_id,)
                ).fetchone()
        except sqlite3.Error:
            return None
        if not row:
            return None
        ingredients = json.loads(row["ingredients_json"])
        instructions = json.loads(row["instructions_json"])
        record = self._record(row, ingredients, instructions)
        record.update({
            "ingredients": [
                {"id": f"ingredient-{index}", "name": text, "quantity": None, "unit": "", "note": None}
                for index, text in enumerate(ingredients)
            ],
            "steps": [{"text": text, "minutes": None} for text in instructions],
            "nutrition": self._nutrition(row),
            "nutrition_basis": "per_100g" if row["protein_per_100g"] is not None else None,
        })
        return record

    def minimum_servings(self, slug: str) -> int | None:
        recipe_id = self.recipe_id(slug)
        if not recipe_id or not self.available:
            return None
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT protein_total, calories_total FROM recipes WHERE recipe_id = ?", (recipe_id,)
                ).fetchone()
        except sqlite3.Error:
            return None
        return self._minimum_servings(row) if row else None

    @staticmethod
    def _minimum_servings(row) -> int | None:
        """Smallest confirmed serving count that yields a plausible portion, if one exists.

        A label that says "verified nutrition" has to mean the user can actually reach a credible
        number, otherwise the card promises something the calculation then refuses. Batch records
        are the hard case: their totals are real but only divide into a portion once the serving
        count is high enough, so the UI can say "at least N servings" instead of dead-ending.
        """
        if row["protein_total"] is None:
            return None
        for servings in range(1, MAX_CONFIRMED_SERVINGS + 1):
            if (
                row["protein_total"] / servings <= MAX_SERVING_PROTEIN_G
                and row["calories_total"] / servings <= MAX_SERVING_CALORIES
            ):
                return servings
        return None

    def nutrition_for_servings(self, slug: str, servings: int) -> dict | None:
        recipe_id = self.recipe_id(slug)
        if not recipe_id or not self.available:
            return None
        with self._connect() as connection:
            row = connection.execute(
                """SELECT protein_total, calories_total, fat_total, recipe_weight_g
                   FROM recipes WHERE recipe_id = ?""", (recipe_id,)
            ).fetchone()
        if not row or row["protein_total"] is None or row["calories_total"] is None or row["fat_total"] is None:
            return None
        nutrition = {
            "protein": round(row["protein_total"] / servings, 1),
            "calories": round(row["calories_total"] / servings, 1),
            "fat": round(row["fat_total"] / servings, 1),
            "carbs": None,
        }
        # Last line of defence. Import validation keeps stored totals physically plausible, but a
        # user-chosen serving count can still divide a large recipe into an impossible portion.
        # Failing closed here is what stops a nonsense number from ever reaching the screen.
        if nutrition["protein"] > MAX_SERVING_PROTEIN_G or nutrition["calories"] > MAX_SERVING_CALORIES:
            return None
        return {
            "servings": servings,
            "nutrition": nutrition,
            "basis": "user_confirmed_servings",
            "recipe_weight_g": row["recipe_weight_g"],
            "source": "Recipe1M ingredient-level nutrition subset",
        }

    def cached_image(self, recipe_id: str) -> Path | None:
        if not re.fullmatch(r"[a-f0-9]{10}", recipe_id) or not self.available:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT image_url, image_id FROM recipes WHERE recipe_id = ?", (recipe_id,)
            ).fetchone()
        if not row or not row["image_url"]:
            return None
        suffix = Path(row["image_id"] or "image.jpg").suffix.lower()
        suffix = suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
        destination = self.image_cache / f"{recipe_id}{suffix}"
        if destination.is_file():
            return destination
        parsed = urlparse(row["image_url"])
        if parsed.scheme not in {"http", "https"}:
            return None
        try:
            request = urllib.request.Request(row["image_url"], headers={"User-Agent": "ProteinPantry/1.0"})
            with urllib.request.urlopen(request, timeout=8) as response:
                content_type = response.headers.get_content_type()
                if content_type not in {"image/jpeg", "image/png", "image/webp"}:
                    return None
                payload = response.read(8 * 1024 * 1024 + 1)
            if len(payload) > 8 * 1024 * 1024:
                return None
            self.image_cache.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_bytes(payload)
            temporary.replace(destination)
            return destination
        except (OSError, ValueError):
            return None

    @staticmethod
    def recipe_id(slug: str) -> str | None:
        match = re.fullmatch(r"r1m-([a-f0-9]{10})", slug)
        return match.group(1) if match else None

    @staticmethod
    def _fts_query(terms: list[str]) -> str:
        query_tokens = []
        for term in terms:
            query_tokens.extend(QUERY_TOKEN_RE.findall(normalize(term)))
        unique = [token for token in dict.fromkeys(query_tokens) if token not in QUERY_STOPWORDS][:12]
        return " OR ".join(f'"{token}"' for token in unique)

    @staticmethod
    def _nutrition(row: sqlite3.Row) -> dict | None:
        if row["protein_per_100g"] is None:
            return None
        return {
            "protein": row["protein_per_100g"],
            "calories": row["calories_per_100g"],
            "fat": row["fat_per_100g"],
            "carbs": None,
        }

    def _record(self, row: sqlite3.Row, ingredients: list[str], instructions: list[str] | None = None) -> dict:
        nutrition = self._nutrition(row)
        minimum = self._minimum_servings(row)
        photo = None
        if row["image_url"]:
            photo = {
                "url": f"/api/recipe1m/images/{row['recipe_id']}",
                "author": "Source recipe",
                "license": "Source terms apply",
            }
        return {
            "slug": f"r1m-{row['recipe_id']}",
            "name": row["title"],
            "summary": "A locally indexed Recipe1M recipe. Open it for the original ingredients and method.",
            "cuisine": "Cuisine not listed",
            "country": "Country not listed",
            "category": "main",
            "diets": [],
            "difficulty": None,
            "servings": None,
            "total_minutes": None,
            # Search cards compare per-serving values, which Recipe1M does not provide.
            "protein_g": None,
            "calories": None,
            "nutrition_available": minimum is not None,
            "minimum_servings": minimum,
            "photo": photo,
            "ingredients_text": ingredients,
            "instructions_text": instructions or [],
            "lexical_score": float(row["lexical_score"]) if "lexical_score" in row.keys() else 0.0,
            "corpus": "recipe1m",
            "source": {
                "attribution": "Recipe1M local corpus",
                "homepage": row["source_url"],
                "license": "Local dataset; original source terms apply",
                "licenseUrl": "http://pic2recipe.csail.mit.edu/",
            },
        }


def _phrase_matches(term: str, value: str) -> bool:
    term_words = term.split()
    value_words = value.split()
    for index in range(len(value_words) - len(term_words) + 1):
        candidate = value_words[index:index + len(term_words)]
        if all(left == right or left.rstrip("s") == right.rstrip("s") for left, right in zip(term_words, candidate)):
            return True
    return False


recipe1m_index = Recipe1MIndex()
