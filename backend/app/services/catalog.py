import json
import math
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from .pantry import normalize, parse_pantry
from .pantry_refinement import pantry_refinement
from .recipe1m import recipe1m_index
from .safety import recipe_is_safe


DATA_PATH = Path(__file__).parents[2] / "data" / "unitools-recipes-v2.json"
TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize(text))


DERIVED_FORMS = {
    "chicken": {"stock", "broth", "bouillon"},
    "rice": {"noodle", "noodles", "paper", "flour", "vinegar", "wine", "milk"},
}
PASTA_FORMS = {"spaghetti", "penne", "macaroni", "linguine", "fettuccine", "rigatoni", "tagliatelle"}


def ingredient_matches(term: str, ingredient: str) -> bool:
    if term == ingredient:
        return True
    if term == "pasta" and PASTA_FORMS.intersection(ingredient.split()):
        return True
    if term not in ingredient and ingredient not in term:
        return False
    blockers = DERIVED_FORMS.get(term, set())
    return not blockers.intersection(ingredient.split())


def exclusion_matches(term: str, ingredient: str) -> bool:
    term_words = term.split()
    ingredient_words = ingredient.split()
    for start in range(len(ingredient_words) - len(term_words) + 1):
        candidate = ingredient_words[start:start + len(term_words)]
        if all(left == right or left.rstrip("s") == right.rstrip("s") for left, right in zip(term_words, candidate)):
            return True
    return False


class RecipeCatalog:
    def __init__(self, local_index=None):
        self.recipes: list[dict] = []
        self.by_slug: dict[str, dict] = {}
        self.known_terms: set[str] = set()
        self.bm25: BM25Okapi | None = None
        self.meta: dict = {}
        self.local_index = local_index or recipe1m_index

    def load(self) -> None:
        if self.recipes:
            return
        raw = json.loads(DATA_PATH.read_text())
        countries = {country["code"]: country for country in raw["countries"]}
        self.meta = {key: raw[key] for key in ("name", "version", "license", "licenseUrl", "attribution", "homepage")}
        docs = []
        for item in raw["recipes"]:
            if not recipe_is_safe(item):
                continue
            country = countries.get(item["country"], {})
            item["cuisine"] = country.get("cuisine", {}).get("en", "Global cuisine")
            item["countryName"] = country.get("name", {}).get("en", item["country"])
            item["totalMinutes"] = item.get("prepMinutes", 0) + item.get("cookMinutes", 0)
            item["source"] = self.meta
            names = []
            for ingredient in item["ingredients"]:
                name = normalize(ingredient["name"]["en"])
                names.extend([name, normalize(ingredient["id"])])
                self.known_terms.update([name, normalize(ingredient["id"])])
            document = " ".join([
                item["name"]["en"], item.get("nativeName") or "",
                item.get("summary", {}).get("en", ""), item["cuisine"], item["category"],
                " ".join(names),
            ])
            docs.append(tokens(document))
            self.recipes.append(item)
            self.by_slug[item["slug"]] = item
        self.bm25 = BM25Okapi(docs, k1=1.2, b=0.75)
        self.known_terms.update(self.local_index.known_terms)

    def summary(self, recipe: dict) -> dict:
        photo = recipe.get("photo")
        return {
            "slug": recipe["slug"], "name": recipe["name"]["en"],
            "summary": recipe.get("summary", {}).get("en", ""),
            "cuisine": recipe["cuisine"], "country": recipe["countryName"],
            "category": recipe["category"], "diets": recipe.get("diets", []),
            "difficulty": recipe.get("difficulty"), "servings": recipe["baseServings"],
            "total_minutes": recipe["totalMinutes"],
            "protein_g": recipe["nutritionPerServing"]["protein"],
            "calories": recipe["nutritionPerServing"]["calories"],
            "photo": photo,
            "corpus": "unitools",
        }

    def detail(self, slug: str) -> dict | None:
        recipe = self.by_slug.get(slug)
        if not recipe:
            return self.local_index.detail(slug)
        result = self.summary(recipe)
        result.update({
            "ingredients": [{
                "id": ingredient["id"], "name": ingredient["name"]["en"],
                "quantity": ingredient.get("quantity"), "unit": ingredient.get("unit"),
                "note": (ingredient.get("note") or {}).get("en"),
            } for ingredient in recipe["ingredients"]],
            "steps": [{"text": step["text"]["en"], "minutes": step.get("minutes")} for step in recipe["steps"]],
            "nutrition": recipe["nutritionPerServing"], "source": recipe["source"],
        })
        return result

    def nutrition_for_servings(self, slug: str, servings: int) -> dict | None:
        recipe = self.by_slug.get(slug)
        if recipe:
            return {
                "servings": recipe["baseServings"],
                "nutrition": recipe["nutritionPerServing"],
                "basis": "source_per_serving",
                "source": self.meta["attribution"],
            }
        return self.local_index.nutrition_for_servings(slug, servings)

    def featured(self, limit: int = 12, category: str | None = None) -> list[dict]:
        pool = [recipe for recipe in self.recipes if not category or recipe["category"] == category]
        pool.sort(key=lambda recipe: (
            recipe["country"] != "IN",
            -recipe["nutritionPerServing"]["protein"],
            recipe["totalMinutes"],
        ))
        return [self.summary(recipe) for recipe in pool[:limit]]

    def search(self, pantry_text: str, target: float, preferred_minutes: int | None, exclusions: list[str], limit: int) -> dict:
        parsed = pantry_refinement.refine(
            pantry_text, parse_pantry(pantry_text, self.known_terms), self.known_terms,
        )
        core_terms = parsed["core"] or parsed["recognized"]
        # Retrieval is driven by meal-defining ingredients. Staples and vague seasoning phrases
        # may explain pantry coverage but must not outrank a stronger core-ingredient match.
        query_terms = core_terms or parsed["recognized"] or parsed["display_terms"]
        scores = self.bm25.get_scores(tokens(" ".join(query_terms))) if self.bm25 else []
        max_lexical = max((float(score) for score in scores), default=0.0)
        excluded = {normalize(value) for value in exclusions}
        ranked = []
        for index, recipe in enumerate(self.recipes):
            ingredient_terms = {
                normalize(ingredient["name"]["en"]) for ingredient in recipe["ingredients"]
            } | {normalize(ingredient["id"]) for ingredient in recipe["ingredients"]}
            if excluded and any(any(exclusion_matches(term, ingredient) for term in excluded) for ingredient in ingredient_terms):
                continue
            matched = sorted({term for term in parsed["recognized"] if any(ingredient_matches(term, ing) for ing in ingredient_terms)})
            matched_core = sorted(term for term in core_terms if term in matched)
            if core_terms and not matched_core:
                continue
            essential = [ingredient["name"]["en"] for ingredient in recipe["ingredients"] if ingredient["id"] not in {"salt", "pepper", "oil", "water"}]
            missing = [name for name in essential if not any(term in normalize(name) or normalize(name) in term for term in matched)]
            coverage = len(matched_core) / max(1, len(set(core_terms)))
            full_core_match = bool(core_terms) and coverage == 1
            protein = recipe["nutritionPerServing"]["protein"]
            target_fit = math.exp(-abs(protein - target) / max(8, target * 0.55))
            time_fit = math.exp(-abs(recipe["totalMinutes"] - preferred_minutes) / max(15, preferred_minutes * 0.5)) if preferred_minutes else 0
            lexical = (float(scores[index]) / max_lexical * 6) if len(scores) and max_lexical > 0 else 0.0
            title = normalize(recipe["name"]["en"])
            title_match_count = sum(1 for term in core_terms if ingredient_matches(term, title))
            title_fit = title_match_count * 2.2
            score = lexical + coverage * 8 + title_fit + target_fit * 2 + time_fit * 1.5 + (0.8 if recipe["country"] == "IN" else 0) - min(len(missing), 8) * 0.12
            reasons = []
            if full_core_match and len(core_terms) > 1:
                reasons.append("Matches all your main ingredients")
            elif matched:
                reasons.append(f"Uses {len(matched)} pantry ingredient{'s' if len(matched) != 1 else ''}")
            if abs(protein - target) <= 5:
                reasons.append("Close to your protein target")
            elif protein >= target:
                reasons.append("Meets your protein target")
            if recipe["country"] == "IN":
                reasons.append("Indian favourite")
            if preferred_minutes and abs(recipe["totalMinutes"] - preferred_minutes) <= 10:
                reasons.append("Close to your preferred cooking time")
            elif recipe["totalMinutes"] <= 30:
                reasons.append("Ready in 30 minutes or less")
            ranked.append({
                **self.summary(recipe), "available_ingredients": matched,
                "missing_ingredients": missing[:6], "pantry_coverage": round(coverage, 2),
                "matched_core_ingredients": matched_core, "full_core_match": full_core_match,
                "protein_difference_g": round(protein - target, 1), "score": round(score, 3),
                "reasons": reasons[:3] or ["Relevant to your pantry"],
            })
        local_terms = list(dict.fromkeys([*core_terms, *parsed["display_terms"]]))
        local_candidates = self.local_index.search(local_terms, excluded)
        max_local_lexical = max((recipe["lexical_score"] for recipe in local_candidates), default=0.0)
        for recipe in local_candidates:
            ingredient_terms = {normalize(ingredient) for ingredient in recipe["ingredients_text"]}
            matching_text = ingredient_terms | {
                normalize(recipe["name"]),
            }
            terms_to_match = list(dict.fromkeys([*parsed["recognized"], *parsed["display_terms"]]))
            local_core_terms = parsed["display_terms"] if parsed["mode"] == "locally_refined" else (core_terms or terms_to_match)
            matched = sorted({
                term for term in terms_to_match
                if any(ingredient_matches(term, value) for value in matching_text)
            })
            matched_core = sorted(term for term in local_core_terms if term in matched)
            if local_core_terms and not matched_core:
                continue
            coverage = len(matched_core) / max(1, len(set(local_core_terms)))
            full_core_match = bool(local_core_terms) and coverage == 1
            missing = [
                ingredient for ingredient in recipe["ingredients_text"]
                if not any(ingredient_matches(term, normalize(ingredient)) for term in matched)
            ]
            title = normalize(recipe["name"])
            title_fit = sum(1 for term in local_core_terms if ingredient_matches(term, title)) * 2.2
            lexical = recipe["lexical_score"] / max_local_lexical * 6 if max_local_lexical > 0 else 0.0
            score = lexical + coverage * 8 + title_fit - min(len(missing), 8) * 0.12
            reasons = []
            if full_core_match and len(local_core_terms) > 1:
                reasons.append("Matches all your main ingredients")
            elif matched:
                reasons.append(f"Uses {len(matched)} pantry ingredient{'s' if len(matched) != 1 else ''}")
            reasons.append("From your local Recipe1M index")
            ranked.append({
                **{key: value for key, value in recipe.items() if key not in {"ingredients_text", "instructions_text", "lexical_score", "source"}},
                "available_ingredients": matched,
                "missing_ingredients": missing[:6],
                "pantry_coverage": round(coverage, 2),
                "matched_core_ingredients": matched_core,
                "full_core_match": full_core_match,
                "protein_difference_g": None,
                "score": round(score, 3),
                "reasons": reasons[:3],
            })
        ranked.sort(key=lambda item: (
            item["full_core_match"], item["pantry_coverage"],
            len(item["matched_core_ingredients"]), item["score"],
        ), reverse=True)
        return {"parsed_pantry": parsed, "results": ranked[:limit], "total_eligible": len(ranked)}


catalog = RecipeCatalog()
