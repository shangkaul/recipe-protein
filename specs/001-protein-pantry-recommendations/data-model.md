# Data Model

## PantryRequest

- `text: string`
- `protein_target_g: number` (5–100)
- `preferred_minutes: number | null` (soft ranking preference, never an eligibility filter)
- `exclusions: string[]`
- `limit: number` (1–30)

## ParsedPantry

- `recognized: string[]` canonical ingredient IDs
- `display_terms: string[]`
- `unresolved: string[]`

## Recipe

- `slug`, `name`, `summary`, `country`, `cuisine`, `category`, `difficulty`
- `servings`, `prep_minutes`, `cook_minutes`, `total_minutes`
- `nutrition_per_serving { protein_g, calories, fat_g, carbs_g, source }`
- `ingredients[] { id, name, quantity, unit, note }`
- `steps[] { text, minutes }`
- `photo { url, author, license } | null`
- `source { name, url, license, license_url }`

## RankedRecipe

- `recipe: RecipeSummary`
- `available_ingredients: string[]`
- `missing_ingredients: string[]`
- `pantry_coverage: number`
- `protein_difference_g: number`
- `score: number`
- `reasons: string[]`

## Adaptation

- `recipe_slug`, `title`, `servings`
- `changes[] { action, ingredient_id, original_quantity, new_quantity, reason }`
- `ingredients[]`, `steps[]`
- `nutrition_per_serving`
- `validation { valid, errors[] }`
- `model { provider: "ollama", name }`

## Invariants

- A Recipe or Adaptation containing a red-meat term is never eligible for display.
- Source nutrition is immutable for unchanged recipes.
- Adaptation nutrition is produced only after validation and deterministic calculation.
- Unknown or unsupported adaptation ingredients invalidate the adaptation.
