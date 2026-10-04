import json
import re
from pathlib import Path

from .pantry import normalize


REFERENCE_PATH = Path(__file__).parents[2] / "data" / "nutrient-reference.json"


class NutritionReference:
    def __init__(self, path: Path = REFERENCE_PATH):
        raw = json.loads(path.read_text())
        self.source = raw["source"]
        self.foods = {item["id"]: item for item in raw["foods"]}
        self.aliases = {
            normalize(alias): item["id"]
            for item in raw["foods"]
            for alias in [item["id"], item["name"], *item["aliases"]]
        }

    def pantry_foods(self, pantry_text: str) -> dict[str, dict]:
        searchable = [normalize(pantry_text), *(
            normalize(part) for part in re.split(r"[,;\n]+|\band\b|\bplus\b", pantry_text.lower())
        )]
        matched = {}
        for alias, food_id in sorted(self.aliases.items(), key=lambda item: len(item[0]), reverse=True):
            if any(f" {alias} " in f" {value} " for value in searchable):
                matched[food_id] = self.foods[food_id]
        return matched

    def source_foods(self, ingredients: list[dict]) -> set[str]:
        matched = set()
        for ingredient in ingredients:
            value = normalize(f"{ingredient.get('id', '')} {ingredient.get('name', '')}")
            for alias, food_id in self.aliases.items():
                if f" {alias} " in f" {value} ":
                    matched.add(food_id)
        return matched

    def delta_per_serving(self, changes: list, servings: int) -> dict:
        totals = {"protein": 0.0, "calories": 0.0, "fat": 0.0}
        for change in changes:
            food = self.foods[change.ingredient_id]
            factor = change.quantity_g / 100 / servings
            for nutrient in totals:
                totals[nutrient] += food[nutrient] * factor
        return {key: round(value, 1) for key, value in totals.items()}

    @staticmethod
    def add(base: dict, delta: dict) -> dict:
        result = {}
        for key in ("protein", "calories", "fat", "carbs"):
            if base.get(key) is None:
                result[key] = None
            else:
                result[key] = round(float(base[key]) + float(delta.get(key) or 0), 1)
        return result


nutrition_reference = NutritionReference()
