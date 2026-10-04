from dataclasses import dataclass
from typing import Literal

from pydantic import Field, create_model

from .nutrition import NutritionReference, nutrition_reference
from .ollama import LocalModelError, OllamaClient, ollama_client
from .pantry import normalize
from .safety import contains_red_meat


SYSTEM_PROMPT = """You adapt exactly one source recipe using only the allowed pantry ingredients.
Return only the requested schema. Propose one to three add or increase operations in grams. Keep the
dish recognizable and cookable. Every grams value must be a realistic kitchen quantity of 25 g or
more; never propose 1 g, a pinch, or a token amount. Never provide nutrition, servings, substitutions
outside the allowed list, removals, or medical advice. Instruction notes may explain how to
incorporate accepted changes but must not replace the source method."""


# gemma3:1b reliably proposes token quantities (often 1 g), so schema bounds alone are not
# sufficient. A proposal survives only if it adds a practical weight of at least one source
# serving's worth of the ingredient, and moves protein by at least these amounts. Otherwise the
# comparison would show a cosmetic difference, so the proposal is rejected instead.
MINIMUM_QUANTITY_G = 25.0
MAXIMUM_QUANTITY_G = 500.0
# A boost has to stay a boost. Past this much added protein per serving the dish is no longer the
# source recipe with an addition, it is a different meal, so the proposal is refused instead.
MAXIMUM_ADDITION_PER_SERVING_G = 300.0
QUANTITY_STEP_G = 5.0
MINIMUM_PROTEIN_G = 1.0
MEANINGFUL_PROTEIN_FRACTION = 0.02


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
            f"Verified protein per serving before changes: {base_nutrition['protein']} g\n"
            f"Confirmed servings: {servings}\n"
            f"Allowed pantry ingredients: {allowed}\n"
            f"Excluded terms: {sorted(excluded)}"
        )
        proposal_schema = _proposal_schema(tuple(pantry_foods))
        proposal = self.client.structured(SYSTEM_PROMPT, prompt, proposal_schema, timeout=30)
        changes = self._validate(proposal, pantry_foods, source_foods, excluded)
        gap = max(0.0, float(target) - float(base_nutrition["protein"]))
        changes = _scale_to_gap(changes, self.reference, pantry_foods, servings, gap)
        delta = self.reference.delta_per_serving(changes, servings)
        if delta["protein"] < max(MINIMUM_PROTEIN_G, gap * MEANINGFUL_PROTEIN_FRACTION):
            raise AdaptationFailure("no_meaningful_increase")
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
            if change.quantity_g > MAXIMUM_QUANTITY_G:
                raise AdaptationFailure("excessive_quantity")
            seen.add(change.ingredient_id)
        return proposal.changes

    @staticmethod
    def _excluded(food: dict, excluded: set[str]) -> bool:
        aliases = {normalize(alias) for alias in [food["id"], food["name"], *food["aliases"]]}
        return any(term == alias or term in alias or alias in term for term in excluded for alias in aliases)


adaptation_service = AdaptationService()


def _scale_to_gap(changes, reference, pantry_foods: dict, servings: int, gap: float) -> list:
    """Round validated changes up to a kitchen-real quantity and scale the set toward the gap.

    gemma3:1b reliably proposes token amounts such as 1 g. Rather than display a cosmetic
    difference or silently substitute the model's decision, the host sets a practical quantity and
    scales the whole validated set so the protein gap is covered. The model still chooses which
    ingredients to change, the action, and the reasons; Python owns every gram and every number.
    """
    if gap <= 0:
        raise AdaptationFailure("target_already_met")

    # The model's quantities express a ratio between the chosen ingredients. gemma3:1b usually
    # proposes a token amount such as 1 g, so the host owns every gram: it keeps the model's ratio,
    # then solves for the total weight that actually closes the protein gap.
    weights = [max(change.quantity_g, MINIMUM_QUANTITY_G) for change in changes]
    weight_total = sum(weights)
    blend_protein_per_gram = sum(
        pantry_foods[change.ingredient_id]["protein"] / 100 * weight
        for change, weight in zip(changes, weights)
    ) / weight_total

    needed_total_g = gap * servings / blend_protein_per_gram if blend_protein_per_gram > 0 else 0.0
    if needed_total_g / servings > MAXIMUM_ADDITION_PER_SERVING_G:
        raise AdaptationFailure("no_meaningful_increase")

    scaled = []
    for change, weight in zip(changes, weights):
        grams = needed_total_g * weight / weight_total
        grams = round(grams / QUANTITY_STEP_G) * QUANTITY_STEP_G
        grams = min(max(grams, MINIMUM_QUANTITY_G), MAXIMUM_QUANTITY_G)
        scaled.append(change.model_copy(update={"quantity_g": float(grams)}))

    if reference.delta_per_serving(scaled, servings)["protein"] < MINIMUM_PROTEIN_G:
        raise AdaptationFailure("no_meaningful_increase")
    return scaled


def _proposal_schema(ingredient_ids: tuple[str, ...]):
    ingredient_literal = Literal.__getitem__(ingredient_ids)
    change_model = create_model(
        "AllowedModelChange",
        action=(Literal["add", "increase"], ...),
        ingredient_id=(ingredient_literal, ...),
        quantity_g=(float, Field(ge=1, le=1000)),
        reason=(str, Field(min_length=1, max_length=180)),
    )
    return create_model(
        "AllowedModelAdaptation",
        title=(str, Field(min_length=1, max_length=120)),
        changes=(list[change_model], Field(min_length=1, max_length=min(3, len(ingredient_ids)))),
        instruction_notes=(list[str], Field(default_factory=list, max_length=4)),
    )
