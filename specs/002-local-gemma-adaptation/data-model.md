# Data Model

## ModelStatus

- `available: boolean`
- `model: string`
- `reason: ready | service_unavailable | model_missing | timeout | invalid_output`

## PantryRefinementRequest

- `raw_text: string`
- `deterministic_parse: ParsedPantry`
- `candidate_ids: string[]` (bounded server-derived vocabulary)

## PantryRefinement

- `terms[] { raw_term, canonical_id, role: core | basic, confidence }`
- `ignored_terms[] { raw_term, reason }`
- `model_name: string`

## ParsedPantry additions

- `deterministic: string[]`
- `refined: string[]`
- `core: string[]`
- `basics: string[]`
- `unresolved: string[]`
- `mode: deterministic | locally_refined | deterministic_fallback`
- `model_status: ModelStatus`

## AdaptationProposal

- `title: string`
- `changes[] { action, ingredient_id, quantity, unit, reason }`
- `instruction_notes[] { after_step, text }`
- Contains no nutrition fields.

## ValidatedAdaptation

- `source_recipe_slug: string`
- `ingredients[]`
- `steps[]`
- `changes[]`
- `nutrition_per_serving { protein_g, calories, provenance[] }`
- `target_difference_g: number`
- `validation { valid, codes[] }`
- `model { name, local: true }`

## State transitions

```text
deterministic parse
  ├── complete ──> search
  └── ambiguous ──> local refinement
                       ├── valid ──> merged parse ──> search
                       └── failure ──> deterministic fallback ──> search

source recipe ──> proposal ──> schema validation ──> safety validation
  ──> nutrition validation ──> display
  any failure ──> reject proposal; preserve source recipe
```
