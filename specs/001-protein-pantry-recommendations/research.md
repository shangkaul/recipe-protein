# Research: Protein Pantry Recommendations

**Date**: 2026-10-04  
**Status**: Approved for MVP implementation

## Recipe corpus decision

### Selected: UniTools World Recipes v2

- 501 recipes from 127 countries.
- CC BY-SA 4.0 dataset with dataset-level attribution and per-photo licensing metadata.
- Includes stable slug, country/cuisine, category, diets, difficulty, servings, preparation and
  cooking time, per-serving protein/calories, structured quantities, instructions, and source photo.
- The downloaded snapshot is `backend/data/unitools-recipes-v2.json` (2.6 MB).
- Initial exclusion audit: 501 total, 286 eligible after conservative red-meat keyword filtering,
  six eligible Indian recipes, and an eligible protein range of 1–56 g per serving.

**Decision**: Use this as the bundled public MVP corpus. Retain source nutrition for unchanged
recipes and attribution in the interface.

### Rejected as primary: Recipe1M nutrition subset

- Local file contains 51,235 recipes and complete title/ingredient/instruction/nutrition arrays.
- No serving field, cuisine, tags, or time.
- Fraction parsing corruption turns values such as `1/2` into `12`; 4,881 recipes calculate above
  10 kg and 4,455 above 500 g protein.
- Dataset access and redistribution conditions are less suitable for a public release than UniTools.

**Decision**: Keep only as an optional, user-supplied private retrieval corpus. Do not commit or
deploy it and do not use it as the nutrition authority.

## Retrieval

Use BM25 over title, cuisine, ingredient IDs/names, summary, and category. Normalize pantry terms
through a deterministic synonym map before tokenization. Final ranking combines BM25 relevance,
pantry coverage, missing-ingredient penalty, target-protein distance, time fit, and a modest Indian
cuisine preference. Dietary exclusion is a hard pre-filter, never a scoring feature.

## Local model

Use Ollama's local HTTP API with structured JSON output. Default model is configurable and documented
as `gemma3:1b`; no cloud fallback is allowed. The model receives one retrieved recipe, the normalized
pantry, target, and a closed set of allowed substitution ingredients. Its output is schema-validated,
checked for red meat and unknown ingredients, and rejected on failure.

## Nutrition

- Unchanged recipes display UniTools per-serving values and provenance.
- Adaptation changes are limited to known ingredient/quantity operations.
- Nutrition changes are deterministic from a local, attributed nutrient table; model-provided
  nutrition is ignored.
- Unsupported ingredient changes are rejected rather than estimated.

## PWA and deployment

The React shell is installable and caches static assets and the most recently fetched public recipe
responses. Search and adaptation clearly report when the household Flask API is unavailable. The
primary privacy-preserving flow runs on the local network; a demonstration deployment may use the
same container without a cloud AI service.

## References

- UniTools dataset: https://theunitools.com/en/data
- Dataset snapshot: https://theunitools.com/data/unitools-recipes-v1.json
- Recipe1M release: http://wednesday.csail.mit.edu/temporal/release/
- USDA FoodData Central API: https://fdc.nal.usda.gov/api-guide
- Ollama structured outputs: https://ollama.com/blog/structured-outputs
