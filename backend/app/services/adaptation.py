from dataclasses import dataclass
from typing import Literal

from pydantic import Field, create_model

from .nutrition import NutritionReference, nutrition_reference
from .ollama import LocalModelError, OllamaClient, ollama_client
from .pantry import normalize
from .safety import contains_red_meat


SYSTEM_PROMPT = """You adapt exactly one source recipe using only the allowed pantry ingredients.
Return only the requested schema. Propose one to three add or increase operations in grams. Keep the
dish recognizable and cookable. Never provide nutrition, servings, substitutions outside the
allowed list, removals, or medical advice. Instruction notes may explain how to incorporate accepted
changes but must not replace the source method."""


@dataclass
class AdaptationFailure(RuntimeError):
    reason: str

    def __str__(self) -> str:
        return self.reason


class AdaptationService:
    def __init__(
        self,
        client: OllamaClient = ollama_client,
        reference: NutritionReference = nutrition_reference,
    ):
        self.client = client
        self.reference = reference

    def adapt(
        self,
        recipe: dict,
        pantry: str,
        target: float,
        exclusions: list[str],
        servings: int,
        base_nutrition: dict,
    ) -> dict:
        if float(base_nutrition["protein"]) >= target:
            raise AdaptationFailure("target_already_met")
        pantry_foods = self.reference.pantry_foods(pantry)
        excluded = {normalize(value) for value in exclusions}
        pantry_foods = {
            food_id: food for food_id, food in pantry_foods.items()
            if not self._excluded(food, excluded) and not contains_red_meat(" ".join(food["aliases"]))
        }
        if not pantry_foods:
            raise AdaptationFailure("no_supported_pantry_ingredients")

        source_foods = self.reference.source_foods(recipe["ingredients"])
        allowed = [{
            "ingredient_id": food_id,
            "name": food["name"],
            "source_contains": food_id in source_foods,
        } for food_id, food in pantry_foods.items()]
        prompt = (
            f"Source title: {recipe['name']}\n"
            f"Source ingredients: {[item['name'] for item in recipe['ingredients']]}\n"
            f"Source method: {[step['text'] for step in recipe['steps']]}\n"
            f"Protein target per serving: {target} g\n"
            f"Confirmed servings: {servings}\n"
            f"Allowed pantry ingredients: {allowed}\n"
            f"Excluded terms: {sorted(excluded)}"
        )
        proposal_schema = _proposal_schema(tuple(pantry_foods))
        proposal = self.client.structured(SYSTEM_PROMPT, prompt, proposal_schema, timeout=30)
        changes = self._validate(proposal, pantry_foods, source_foods, excluded)
        delta = self.reference.delta_per_serving(changes, servings)
        adapted_nutrition = self.reference.add(base_nutrition, delta)
        return {
            "title": proposal.title,
            "source_slug": recipe["slug"],
            "servings": servings,
            "changes": [{
                **change.model_dump(),
                "name": pantry_foods[change.ingredient_id]["name"],
                "fdc_id": pantry_foods[change.ingredient_id]["fdc_id"],
            } for change in changes],
            "instruction_notes": proposal.instruction_notes,
            "original_nutrition": base_nutrition,
            "nutrition_delta": delta,
            "adapted_nutrition": adapted_nutrition,
            "protein_difference_g": round(adapted_nutrition["protein"] - target, 1),
            "nutrition_source": self.reference.source,
            "source": recipe["source"],
            "model": self.client.model,
        }

    def _validate(self, proposal, pantry_foods: dict, source_foods: set[str], excluded: set[str]):
        seen = set()
        safety_text = " ".join([
            proposal.title,
            *proposal.instruction_notes,
            *(change.reason for change in proposal.changes),
        ])
        if contains_red_meat(safety_text):
            raise AdaptationFailure("unsafe_proposal")
        for change in proposal.changes:
            if change.ingredient_id not in pantry_foods or change.ingredient_id in seen:
                raise AdaptationFailure("unknown_or_duplicate_ingredient")
            food = pantry_foods[change.ingredient_id]
            if self._excluded(food, excluded):
                raise AdaptationFailure("excluded_ingredient")
            if change.action == "increase" and change.ingredient_id not in source_foods:
                raise AdaptationFailure("ingredient_not_in_source")
            seen.add(change.ingredient_id)
        return proposal.changes

    @staticmethod
    def _excluded(food: dict, excluded: set[str]) -> bool:
        aliases = {normalize(alias) for alias in [food["id"], food["name"], *food["aliases"]]}
        return any(term == alias or term in alias or alias in term for term in excluded for alias in aliases)


adaptation_service = AdaptationService()


def _proposal_schema(ingredient_ids: tuple[str, ...]):
    ingredient_literal = Literal.__getitem__(ingredient_ids)
    change_model = create_model(
        "AllowedModelChange",
        action=(Literal["add", "increase"], ...),
        ingredient_id=(ingredient_literal, ...),
        quantity_g=(float, Field(gt=0, le=500)),
        reason=(str, Field(min_length=1, max_length=180)),
    )
    return create_model(
        "AllowedModelAdaptation",
        title=(str, Field(min_length=1, max_length=120)),
        changes=(list[change_model], Field(min_length=1, max_length=min(3, len(ingredient_ids)))),
        instruction_notes=(list[str], Field(default_factory=list, max_length=4)),
    )
