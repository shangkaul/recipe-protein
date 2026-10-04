# Feature Specification: Protein Pantry Recommendations

**Feature Branch**: `[001-protein-pantry-recommendations]`

**Created**: 2026-10-03

**Status**: Approved — implementation authorized 2026-10-04

**Input**: Help the creator's parents use ingredients they already have to choose familiar,
higher-protein meals and snacks that fit a user-entered per-meal protein target, without uploading
dietary information to a cloud AI service.

## Product Context

### Problem Statement

The target users want to increase protein intake but do not want to search recipe sites, manually
compare nutrition labels, or buy an entirely new set of ingredients. They need a quick way to
describe what is already in the kitchen and receive familiar, feasible meal choices that explain
their approximate protein and calorie content. Generic recipe search does not optimize for a
protein target, account well for messy pantry descriptions, or offer grounded substitutions while
keeping dietary information local.

### Goals

- Turn typed, natural-language pantry input into 20–30 ranked meal options.
- Rank results by ingredient fit, per-meal protein-target fit, dietary safety, and practical use.
- Prefer Indian meals while retaining useful global options.
- Let users select a retrieved recipe and receive a grounded adaptation using available ingredients.
- Show approximate protein and calorie values backed by traceable data.
- Provide practical higher-protein substitutions and snack ideas when they help meet the target.
- Keep pantry, preference, and target information on the local device during the primary journey.
- Provide a mobile-first, installable PWA experience suitable for use in the kitchen.

### Non-Goals

- Diagnosing nutritional deficiencies or calculating how much protein a user medically requires.
- Tracking body weight, health conditions, or a complete daily food diary.
- Generating ungrounded recipes without a retrieved source recipe.
- Supporting restaurant ordering, grocery delivery, barcode scanning, or social features.
- Building cloud-scale recipe search infrastructure for the MVP.
- Recommending beef, lamb, pork, or other red meat.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find Meals From What Is Available (Priority: P1)

A parent types a natural description such as "eggs, leftover rice, spinach going soft, chicken;
30 grams of protein; no more than 30 minutes" and receives 20–30 ranked recipes that use those
ingredients, avoid red meat, and show protein and calorie values per serving.

**Why this priority**: This is the complete minimum-value journey. Without useful retrieval from
real pantry input, adaptation and other features have nothing trustworthy to build on.

**Independent Test**: Enter representative pantry descriptions and verify that the result list is
relevant, contains 20–30 distinct choices when the corpus permits, excludes red meat, identifies
available and missing ingredients, and exposes the target-fit information needed to choose.

**Acceptance Scenarios**:

1. **Given** a pantry description, per-meal protein target, and preferred cooking time, **When** the user
   searches, **Then** the product returns up to 30 ranked recipes and explains each result's pantry
   fit, approximate protein, approximate calories, and total time.
2. **Given** a search with fewer than 20 eligible recipes, **When** results are displayed, **Then**
   the product shows all eligible results and explains that the constraints limited the list rather
   than adding unsafe or irrelevant items.
3. **Given** ingredients that include an unfamiliar spelling or common synonym, **When** the user
   searches, **Then** recognized ingredients are normalized and unresolved terms are shown for
   correction rather than silently ignored.
4. **Given** any search, **When** recipes are ranked, **Then** no recipe containing red meat appears.

---

### User Story 2 - Understand and Choose a Recommendation (Priority: P1)

A parent can compare recommendations without nutrition expertise: each option clearly identifies
what is already available, what is missing, why it ranked highly, and how closely one serving meets
the entered target.

**Why this priority**: A long list is not useful unless the ranking and nutrition are understandable
and trusted.

**Independent Test**: Present results to the target users and verify they can select a feasible meal
without developer assistance or consulting an external nutrition source.

**Acceptance Scenarios**:

1. **Given** ranked results, **When** a user reviews a card, **Then** they can see ingredient
   coverage, missing ingredients, protein, calories, time, cuisine, and source attribution.
2. **Given** a recipe above or below the target, **When** it is displayed, **Then** the difference
   from the target is stated in grams without judging the user's target.
3. **Given** approximate nutrition values, **When** they are shown, **Then** the interface labels
   them as estimates and provides their data provenance.

---

### User Story 3 - Adapt a Retrieved Recipe (Priority: P2)

After choosing a recipe, a parent asks for an adaptation that uses more of the available pantry,
removes unavailable ingredients, respects the time and red-meat constraints, and moves the recipe
toward the entered protein target without changing its identity beyond recognition.

**Why this priority**: Adaptation is the load-bearing open-model feature and turns generic retrieval
into help for one real household.

**Independent Test**: Select a retrieved recipe, adapt it against a known pantry, and verify that the
adapted ingredients and steps remain cookable, all changes are explicit, nutrition is recalculated,
and the source recipe remains identifiable.

**Acceptance Scenarios**:

1. **Given** a selected recipe and available ingredients, **When** adaptation succeeds, **Then** the
   product shows the original recipe, every proposed change, updated steps, and recalculated protein
   and calories.
2. **Given** a proposed adaptation containing an unknown ingredient, red meat, impossible quantity,
   or unverifiable nutrition, **When** it is validated, **Then** it is rejected or corrected before
   display and the original recipe remains available.
3. **Given** the local adaptation capability is unavailable, **When** the user requests adaptation,
   **Then** the product clearly disables adaptation while preserving search, comparison, and source
   recipe access; it does not send data to a cloud model.

---

### User Story 4 - Find a Smaller Protein Boost (Priority: P3)

When a full meal is unnecessary, a parent can view practical snacks or small additions using
available ingredients that help close the gap to the entered per-meal target.

**Why this priority**: The original user need includes snacks and substitutions, but useful meal
retrieval and trustworthy adaptation must work first.

**Independent Test**: Enter a pantry containing common snack ingredients and verify that at least
three suitable additions are shown with portions, approximate protein, calories, and missing items.

**Acceptance Scenarios**:

1. **Given** a pantry with eligible snack ingredients, **When** snack suggestions are requested,
   **Then** the product returns at least three options where the corpus permits and explains each
   option's contribution toward the entered target.
2. **Given** no eligible snack in the corpus, **When** suggestions are requested, **Then** the
   product states that no grounded option is available rather than inventing one.

### Edge Cases

- The input is empty, contains only quantities, or includes no recognizable ingredients.
- The user enters duplicate ingredients, plural forms, spelling variants, or mixed Hindi/English
  food terms written in Latin script.
- The requested target is zero, negative, implausibly high, or not numeric.
- Ingredient exclusions reduce the eligible set below 20 recipes or to zero.
- A recipe has incomplete nutrition, quantities, source attribution, or license information.
- An otherwise suitable recipe contains a red-meat-derived ingredient such as stock, gelatin, or
  rendered fat.
- A retrieved recipe meets protein needs but requires too many unavailable ingredients.
- Multiple recipes are near-duplicates or variations of the same dish.
- The local adaptation capability times out, returns malformed output, or proposes an unsafe item.
- The adapted quantity or serving count cannot be mapped to known nutrition data.
- A dataset update changes identifiers or removes a previously available recipe.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST accept a typed natural-language pantry description.
- **FR-002**: The product MUST accept a user-entered per-meal protein target in grams and MUST NOT
  calculate or recommend a target from personal health data.
- **FR-003**: The product MUST accept a preferred cooking time and optional ingredient exclusions.
  Cooking time MUST influence ranking but MUST NOT exclude an otherwise eligible recipe.
- **FR-003a**: Users MUST be able to enter one or more optional excluded ingredients as free text;
  any matching recipe MUST be removed before ranking, while red-meat exclusion remains automatic.
- **FR-004**: The product MUST normalize recognized ingredient synonyms and present unresolved input
  terms for correction.
- **FR-005**: The product MUST retrieve and rank up to 30 distinct eligible recipes per search.
- **FR-006**: Ranking MUST consider pantry ingredient coverage, missing ingredients, protein-target
  fit, preferred-time closeness, cuisine preference, and recipe relevance. Recipes matching every
  recognized core pantry ingredient MUST rank above partial matches whenever such recipes exist;
  basic staples MUST NOT outweigh core-ingredient fit.
- **FR-007**: Ranking MUST prefer Indian recipes when relevance is otherwise comparable while still
  allowing global recipes.
- **FR-008**: The product MUST exclude recipes and adaptations containing beef, lamb, pork, other red
  meat, or red-meat-derived ingredients.
- **FR-009**: Each result MUST show recipe name, cuisine, total time, available ingredients, missing
  ingredients, approximate protein and calories per serving, target difference, and source.
- **FR-010**: The product MUST explain the principal reasons each result ranked where it did in
  plain language.
- **FR-011**: The product MUST let the user inspect the original ingredients, quantities, servings,
  and instructions before requesting adaptation.
- **FR-012**: The product MUST let the user request a grounded adaptation of one retrieved recipe to
  better use available ingredients and approach the entered protein target.
- **FR-013**: Adaptation MUST preserve a link to the source recipe and explicitly list all ingredient,
  quantity, and instruction changes.
- **FR-014**: Adaptation MUST be limited to known ingredients and validated dietary constraints.
- **FR-015**: Protein and calorie values MUST come from attributed nutrition data or deterministic
  calculation; generated prose MUST NOT be used as a nutrition source.
- **FR-016**: Nutrition MUST be recalculated after any ingredient, quantity, or serving change.
- **FR-017**: The product MUST reject an adaptation that cannot be validated and keep the original
  recipe usable.
- **FR-018**: The product MUST provide grounded higher-protein substitutions and snack ideas where
  the recipe corpus and known nutrition data support them.
- **FR-019**: The product MUST remain usable for search and comparison when local adaptation is
  unavailable and MUST NOT silently call a cloud model.
- **FR-020**: Pantry text, exclusions, target, and adaptation prompts MUST remain on the local device
  during the primary journey.
- **FR-021**: Every included recipe, image, and nutrition record MUST carry the attribution and
  licensing information required by its source.
- **FR-022**: The product MUST clearly state that nutrition values are approximate and that the
  product does not provide medical advice.
- **FR-023**: The primary journey MUST be keyboard-operable and use readable text, contrast, labels,
  and focus states.
- **FR-024**: The MVP MUST NOT require user registration or store a health profile.
- **FR-025**: Dataset adoption MUST be blocked until a documented audit confirms license,
  attribution, required fields, cuisine coverage, red-meat filtering feasibility, and nutrition
  completeness.
- **FR-026**: The product MUST be a mobile-first installable PWA with a cached application shell,
  responsive layouts, and clear offline/unavailable states for features requiring the local API.

### Key Entities *(include if feature involves data)*

- **Pantry Request**: The user's original text, recognized and unresolved ingredients, per-meal
  target, preferred cooking time, exclusions, and cuisine preference for one search.
- **Recipe**: A licensed source recipe with identity, cuisine, meal category, servings, ingredients,
  quantities, instructions, times, dietary attributes, and source attribution.
- **Ingredient**: A canonical food identity with synonyms, dietary flags, unit mappings, and a link
  to traceable nutrition information.
- **Nutrition Record**: Attributed protein and calorie values with quantity basis, source, and any
  confidence or approximation metadata.
- **Ranked Recommendation**: A recipe plus pantry coverage, missing ingredients, target difference,
  ranking explanation, and eligibility status for one pantry request.
- **Recipe Adaptation**: A validated derivative of a source recipe containing explicit changes,
  adapted instructions, recalculated nutrition, validation result, and source reference.
- **Dataset Audit**: A decision record covering provenance, license, attribution, schema coverage,
  cuisine distribution, exclusion feasibility, nutrition completeness, and known quality issues.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each target parent can enter a pantry, review recommendations, and choose a feasible
  meal in under three minutes without developer assistance.
- **SC-002**: At least 90% of 30 representative pantry phrases resolve all common ingredients or
  explicitly identify unresolved terms; none are silently discarded.
- **SC-003**: For at least 80% of 20 representative pantry searches, the top 10 contains five or
  more human-judged feasible recipes, provided the audited corpus contains five eligible matches.
- **SC-004**: Every eligible search returns 20–30 distinct recommendations within three seconds on
  the designated demonstration device; constrained searches return all eligible recipes with a
  clear explanation.
- **SC-005**: Across the full indexed corpus and all adaptation tests, zero displayed recipes contain
  red meat or red-meat-derived ingredients.
- **SC-006**: Protein and calorie values shown for unchanged source recipes match their attributed
  source, and values for adapted recipes reproduce from ingredient quantities within the documented
  rounding tolerance.
- **SC-007**: At least 90% of a 20-case adaptation test set produces a cookable, constraint-compliant
  result or a clear validation failure; no invalid adaptation is displayed as valid.
- **SC-008**: A target parent rates at least 4 of the top 10 recommendations as something they would
  realistically cook for each of three representative pantry searches.
- **SC-009**: A complete local demonstration works without internet access after initial setup, and
  no pantry or dietary input is transmitted externally.
- **SC-010**: Every displayed recipe and image has complete source attribution and license terms.

## Assumptions

- The target users are omnivores who eat poultry, fish, eggs, dairy, and plant proteins but want all
  red meat excluded.
- Indian meals are preferred, but familiar global recipes are acceptable.
- The user knows or has been given an appropriate protein target and enters a per-meal value; the
  product neither verifies nor prescribes it.
- The MVP is used by one household on a local computer and requires no account, synchronization, or
  long-term profile. A phone may install the PWA and connect to the household's local API.
- Recipe adaptation is optional; retrieval and nutrition comparison remain valuable without it.
- A 500–1,000 recipe corpus is expected to be enough for the MVP if the dataset audit confirms an
  adequate Indian-food and protein distribution. The final corpus and nutrition source remain a
  research decision for technical planning.
- Retrieval, normalization, and interaction behavior will be implemented and tested specifically
  for Protein Pantry.
- Nutrition is planning guidance, not a substitute for a clinician or dietitian.

## Research Decisions Resolved for MVP

1. UniTools World Recipes v2 is the public MVP corpus because it has explicit CC BY-SA licensing,
   serving nutrition, quantities, instructions, cuisine, time, and per-photo license metadata.
2. Source recipe nutrition is displayed unchanged for unadapted recipes; adapted nutrition must be
   deterministically recalculated from attributed ingredient data before release.
3. Recipe1M remains an optional private retrieval experiment and is not bundled or used as the MVP
   nutrition authority because servings are absent and fraction corruption was measured.
4. Representative pantry-query and adaptation fixtures are versioned with the tests before ranking
   or model-output tuning claims are made.
