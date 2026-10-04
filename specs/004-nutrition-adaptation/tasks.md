# Tasks: Deterministic Nutrition and Grounded Adaptation

- [x] T001 Add progress-preserving pantry-search loading UI and accessibility tests.
- [x] T002 Add attributed USDA nutrient reference and pure nutrition calculator.
- [x] T003 Import validated Recipe1M whole-recipe weights and nutrient totals.
- [x] T004 Add confirmed-serving nutrition request and API contract.
- [x] T005 Add closed adaptation schemas, prompt, and local model service.
- [x] T006 Validate pantry ingredients, source increases, exclusions, red meat, and gram bounds.
- [x] T007 Calculate deterministic adaptation deltas and target difference.
- [x] T008 Build serving confirmation and original-versus-adapted detail UI.
- [x] T009 Test calculations, malformed output, safety, fallback, API, and UI states.
- [x] T010 Rebuild the private index and record full local evidence.
- [x] T011 Update README, run full validation, and raise the combined checkpoint PR.

## Full-index evidence

- Schema: v2
- Source records scanned: 1,029,720
- Safe indexed records: 818,408
- Records with image metadata: 323,090
- Records with fully validated ingredient-level nutrition totals: 17,200
- Build time: 100.11 seconds
- Index size: 1,639,124,992 bytes

## Correction recorded during release hardening

The first schema-v2 build reported 47,047 nutrition-ready records. Reviewing live output exposed
per-serving values such as 1573.2 g protein and 15200.4 kcal, because import validation only
checked per-100g values and ratios. Garbled Recipe1M quantities inflated single recipes to 11 kg
while still producing believable per-100g numbers, so they passed every check.

Two guards were added and the index rebuilt:

1. Import validation now enforces absolute scale: recipe weight at most 10 kg, a single ingredient
   at most 5 kg, energy density at most 6 kcal/g, and protein no greater than the mass of food.
2. Serving-time validation refuses any calculated portion above 150 g protein or 1500 kcal, so a
   mis-parsed yield cannot divide into an impossible serving no matter what is stored.

The stricter import rules reduce the nutrition-ready set to 17,200 records. That is the intended
trade: fewer recipes support serving-based nutrition, and none of them display a wrong number.

A follow-up review found the label had become untrustworthy: cards read **Verified nutrition**
whenever totals existed, but the serving guard could still refuse those same recipes, so a verified
result dead-ended with a bare error. Each recipe now carries the smallest serving count that yields
a plausible portion. The label is driven by that, the search filter mirrors it in SQL, and the API
returns the floor so the detail view can correct the input and explain why. Verified recipes
labelled verified now produce a real number in every case.
