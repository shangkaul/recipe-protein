# Feature Specification: Deterministic Nutrition and Grounded Adaptation

**Branch**: `feat/nutrition-adaptation`  
**Created**: 2026-10-04  
**Status**: Approved — combined checkpoint authorized 2026-10-04

## Goal

Turn one retrieved source recipe into a safely adapted version using local Gemma while keeping
servings, nutrient inputs, arithmetic, exclusions, and final acceptance deterministic. Improve the
search wait state without blocking browsing.

## Requirements

- **FR-001**: Search MUST show a visible, screen-reader-announced progress state while retaining the
  current results until replacements arrive.
- **FR-002**: Recipe1M per-serving nutrition MUST require an explicit source yield or a user-confirmed
  serving count; the model MUST NOT choose servings.
- **FR-003**: Imported Recipe1M totals MUST be calculated only from finite, plausible ingredient
  weights and nutrient records and MUST retain their per-100g provenance.
- **FR-004**: Adaptation MUST begin from exactly one retrieved source recipe.
- **FR-005**: Gemma MAY propose only closed-schema add/increase operations, reasons, and instruction
  notes. It MUST NOT return trusted nutrition or serving values.
- **FR-006**: Proposed ingredients MUST come from the attributed local nutrient reference and be
  present in the pantry; quantities MUST be bounded grams.
- **FR-007**: Exclusions and red-meat safety MUST be applied before and after adaptation.
- **FR-008**: Python MUST calculate all nutrition deltas and target differences from source values,
  confirmed servings, and attributed per-100g records.
- **FR-009**: Invalid, unavailable, timed-out, unsafe, or unverifiable proposals MUST fail closed while
  preserving the original recipe.
- **FR-010**: The UI MUST compare original and adapted nutrition, list every accepted change and
  reason, retain source attribution, and label values approximate.
- **FR-011**: Pantry, recipe, target, exclusions, and model output MUST remain on loopback services.

## Acceptance Scenarios

1. Searching keeps existing cards visible and announces “Finding meals” until ranked results arrive.
2. A Recipe1M recipe with validated totals shows per-serving protein/calories only after the user
   confirms servings.
3. An allowed pantry protein can be added in grams; Python reproduces the displayed nutrition delta.
4. Unknown, excluded, red-meat, non-pantry, unsupported, or excessive model changes are rejected.
5. Stopped Ollama leaves the original recipe usable and provides an actionable local error.

## Non-goals

- Calculating complete nutrition for Recipe1M records outside its validated nutrition subset.
- Guessing serving yield or ingredient weights.
- Rewriting the source recipe or replacing its attribution.
- Cloud inference or runtime cloud nutrition lookups.
