# Plan: Deterministic Nutrition and Grounded Adaptation

## Architecture

1. Extend the private Recipe1M index with validated whole-recipe weight and nutrient totals derived
   from its ingredient-level nutrition subset.
2. Add a pure nutrition service that divides source totals by confirmed servings and calculates
   adaptation deltas from a compact USDA FoodData Central reference committed with provenance.
3. Add an adaptation service that gives local Gemma one source recipe, pantry terms, exclusions,
   target, and the closed nutrient-reference ingredient list.
4. Validate every proposal independently of its schema: canonical ID, pantry presence, source
   requirement for increases, exclusions, safety, quantity bounds, and reproducible arithmetic.
5. Add per-serving confirmation and original/adapted comparison to the recipe drawer.
6. Keep cards mounted during search and layer a concise progress state over the results region.

## Trust boundary

Gemma performs language work only. Model-supplied numbers are accepted solely as bounded proposed
gram changes, never as facts about the source recipe. Serving yield, source nutrition, nutrient
records, calculations, and acceptance are host-controlled. If evidence is incomplete, the feature
fails closed.

## Nutrient source

USDA FoodData Central records are public-domain and stored locally with FDC IDs, descriptions,
per-100g protein/calories/fat, retrieval date, and source URL. There are no runtime USDA requests.

## API

- `POST /api/recipes/<slug>/nutrition`: confirm servings and return deterministic source nutrition.
- `POST /api/recipes/<slug>/adapt`: validate a local-model proposal and return comparison data.
