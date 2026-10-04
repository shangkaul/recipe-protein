# Feature Specification: Local Pantry Intelligence and Recipe Adaptation

**Feature Branch**: `feat/local-gemma-adaptation`  
**Created**: 2026-10-04  
**Status**: Approved — implementation authorized 2026-10-04  
**Input**: Improve pantry understanding with a local open-weight model and let a parent adapt one
retrieved recipe toward their pantry and protein target without sending dietary data to a cloud AI
service or trusting generated nutrition values.

## Clarifications

### Session 2026-10-04

- **Local model responsibility**: deterministic parsing runs first; Gemma handles ambiguous pantry
  refinement and, in the next checkpoint, grounded adaptation of one selected recipe.
- **Exclusion input**: one optional free-text field supports comma-separated ingredients and acts as
  a hard filter; automatic red-meat exclusion remains active.
- **Failure behavior**: search falls back to direct matches; adaptation fails closed with the source
  recipe still available. There is no cloud-model fallback.
- **Review checkpoints**: pantry refinement and recipe adaptation ship as separate PRs.

## Product Context

### Problem Statement

Deterministic pantry parsing is fast and predictable but cannot anticipate every synonym, mixed
Hindi/English phrase, vague grouping, or misspelling. After retrieval, a source recipe may still
require ingredients the household lacks or may fall short of the user-entered protein target. The
product needs local reasoning for those ambiguous and contextual cases while keeping search,
dietary constraints, nutrition, and source attribution verifiable.

### Goals

- Refine ambiguous pantry phrases into known canonical ingredients using local inference.
- Preserve deterministic parsing as the reliable fallback and visible baseline.
- Let users enter optional ingredients to avoid before search or adaptation.
- Adapt one selected source recipe using available or explicitly allowed ingredients.
- Explain every ingredient or instruction change in plain language.
- Recalculate nutrition deterministically after validated changes.
- Keep all pantry, exclusion, target, recipe, and adaptation data local.

### Non-Goals

- Generating recipes without a retrieved source recipe.
- Letting generated text provide protein or calorie values.
- Silently replacing unavailable local inference with a cloud service.
- Diagnosing nutrition needs or changing the user's protein target.
- Automatically purchasing missing ingredients or maintaining a long-term pantry profile.

## User Scenarios & Testing

### User Story 1 — Understand Ambiguous Pantry Input (Priority: P1)

A parent enters informal pantry language containing aliases, misspellings, mixed Indian English,
or phrases such as “other spices.” The app first performs deterministic parsing, then optionally
uses local inference to refine unresolved terms into known ingredients and classify ingredients as
meal-defining or basic.

**Independent Test**: Submit a fixture set of ambiguous pantry phrases with local inference enabled,
disabled, unavailable, and malformed; confirm the final canonical terms are validated and retrieval
still works in every fallback case.

**Acceptance Scenarios**:

1. **Given** pantry text fully resolved by deterministic rules, **When** search runs, **Then** no
   inference is required and the deterministic result is used.
2. **Given** unresolved or ambiguous terms and local inference is available, **When** refinement
   succeeds, **Then** only known canonical ingredient identifiers are accepted and the interface
   indicates which terms were locally refined.
3. **Given** unavailable, timed-out, malformed, or invalid inference output, **When** search runs,
   **Then** deterministic terms remain usable and unresolved terms remain visible for correction.
4. **Given** optional excluded ingredients, **When** search runs, **Then** recipes containing those
   ingredients are removed before ranking.

---

### User Story 2 — Adapt a Selected Recipe (Priority: P1)

After selecting a retrieved recipe, a parent requests a version that better uses their pantry and
approaches the entered protein target while preserving the dish's recognizable identity.

**Independent Test**: Adapt representative recipes against fixed pantries and verify every proposed
change is explicit, uses an allowed ingredient, respects exclusions, remains cookable, and has
reproducible nutrition or a clear validation failure.

**Acceptance Scenarios**:

1. **Given** a source recipe, pantry, exclusions, and target, **When** adaptation succeeds, **Then**
   the app shows the original and adapted ingredients, changed steps, reasons, source attribution,
   and recalculated per-serving protein and calories.
2. **Given** a proposed unknown ingredient, excluded ingredient, red meat, unsupported quantity,
   ungrounded step, or unverifiable nutrition delta, **When** validation runs, **Then** the output is
   rejected and the original recipe remains available.
3. **Given** local inference is unavailable, **When** adaptation is requested, **Then** the app
   explains how to start the local capability and never sends the request elsewhere.
4. **Given** the adapted recipe cannot safely approach the target using allowed ingredients,
   **When** adaptation completes, **Then** the app keeps the closest validated version and honestly
   states the remaining target difference rather than inventing a change.

### Edge Cases

- Pantry input combines several ingredients without punctuation.
- A synonym could map to more than one ingredient.
- An excluded term is plural, a spelling variant, or part of a compound ingredient.
- Local inference returns valid JSON with unknown identifiers or unsafe prose.
- The selected recipe uses quantities that cannot be converted for nutrition calculation.
- The model proposes changing servings rather than ingredient quantities.
- A proposed change removes the dish's defining ingredient.
- The local model is installed but its service is stopped or still loading.
- Adaptation times out after search has already succeeded.

## Requirements

### Functional Requirements

- **FR-001**: Deterministic pantry parsing MUST run before any model-assisted refinement.
- **FR-002**: Local refinement MUST be limited to unresolved, ambiguous, or role-classification
  cases and MUST return a constrained structured response.
- **FR-003**: Every refined ingredient identifier MUST exist in the current canonical ingredient
  vocabulary before it can influence retrieval.
- **FR-004**: Model failure MUST preserve deterministic recognized terms and visible unresolved
  terms; it MUST NOT block search.
- **FR-005**: The interface MUST distinguish deterministic terms, locally refined terms, basic
  ingredients, and unresolved terms without exposing implementation jargon.
- **FR-006**: Users MUST be able to enter optional free-text ingredient exclusions.
- **FR-007**: Exclusions and automatic red-meat rules MUST be applied before ranking and again before
  displaying an adaptation.
- **FR-008**: Adaptation MUST start from exactly one retrieved source recipe selected by the user.
- **FR-009**: The adaptation request MUST be grounded in the source recipe, parsed pantry,
  exclusions, target, servings, and a closed set of allowed ingredient operations.
- **FR-010**: Model output MUST conform to a documented schema and MUST NOT directly set nutrition.
- **FR-011**: Every proposed ingredient and quantity change MUST be validated before display.
- **FR-012**: Adaptation MUST preserve source identity and explicitly list every change and reason.
- **FR-013**: Protein and calories MUST be recalculated deterministically from attributed nutrition
  records for the final validated quantities.
- **FR-014**: Any output with unverifiable nutrition MUST be rejected rather than partially shown.
- **FR-015**: Search and original recipe detail MUST remain usable when adaptation is unavailable.
- **FR-016**: The product MUST disclose local model readiness and actionable unavailable states.
- **FR-017**: Pantry text, exclusions, targets, and adaptation content MUST remain on the local
  device and MUST NOT be sent to a cloud inference service.
- **FR-018**: The app MUST retain source recipe attribution alongside every adaptation.
- **FR-019**: The app MUST label all nutrition as approximate and MUST NOT provide medical advice.

### Key Entities

- **Pantry Parse**: deterministic terms, locally refined terms, core ingredients, basics, unresolved
  terms, parser mode, and validation result.
- **Ingredient Exclusion**: normalized user-entered term applied as a hard eligibility constraint.
- **Local Model Status**: availability, configured model name, and actionable failure reason.
- **Adaptation Request**: source recipe, pantry parse, exclusions, protein target, and allowed
  ingredient operations.
- **Adaptation Proposal**: structured model output containing changes and instruction notes but no
  trusted nutrition.
- **Validated Adaptation**: accepted changes, final ingredients and steps, deterministic nutrition,
  target difference, source reference, and validation outcome.

## Success Criteria

- **SC-001**: Search remains available in 100% of tests where local inference is stopped, times out,
  or returns invalid output.
- **SC-002**: Across 30 representative pantry phrases, at least 90% of common ingredients resolve or
  are explicitly shown as unresolved; no term is silently discarded.
- **SC-003**: Across the full adaptation test set, zero displayed outputs contain an excluded,
  unknown, or red-meat ingredient.
- **SC-004**: Every displayed adaptation's protein and calorie values reproduce from validated
  quantities within the documented rounding tolerance.
- **SC-005**: At least 90% of 20 representative adaptation cases produce a cookable validated result
  or a specific actionable failure; no invalid proposal is presented as usable.
- **SC-006**: A user can identify what changed, why, and the updated target difference within one
  minute without comparing raw model output.
- **SC-007**: No network request containing pantry, exclusions, target, or recipe content leaves the
  local device during search or adaptation tests.
- **SC-008**: Model-assisted pantry refinement completes within 10 seconds and selected-recipe
  adaptation within 30 seconds on the designated demonstration device in at least 90% of trials.

## Assumptions

- A small local open-weight model is installed separately before model-assisted features are used.
- Deterministic parsing already handles ordinary ingredient lists and remains the default fallback.
- Initial deterministic nutrition changes may be limited to ingredients with attributed local
  records and supported units.
- Adaptation is user-triggered and never runs automatically for every search result.
- One household uses the app without accounts or shared concurrent editing.
