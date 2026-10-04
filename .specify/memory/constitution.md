<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Added principles: Parents-First Value; Deterministic Nutrition; Grounded Local AI;
  Evidence-Driven Retrieval; Small, Reviewable Increments
- Added sections: Product and Safety Constraints; Development Workflow and Quality Gates
- Removed sections: none (template placeholders replaced)
- Added workflow requirement: feature branches and user-approved pull requests
- Follow-up TODOs: enable GitHub branch protection after repository creation
-->
# Recipe Protein Constitution

## Core Principles

### I. Parents-First Value
Every feature MUST make it easier for the target users—the creator's parents—to choose a
familiar, practical, higher-protein meal from ingredients they already have. Product decisions
MUST prioritize clarity, low effort, familiar food, and a useful recommendation over novelty or
feature count. General-purpose functionality MAY be added only after the parents-first journey is
complete and independently usable.

### II. Deterministic Nutrition (NON-NEGOTIABLE)
Protein and calorie values MUST originate from an attributed nutrition source or a deterministic,
testable calculation. A generative model MUST NOT invent, estimate, or silently alter nutritional
values. Adapted recipes MUST be recalculated from their final ingredient quantities. The product
MUST label values as approximate guidance and MUST NOT present medical advice or prescribe a
protein target.

### III. Grounded Local AI
Open-weight AI MUST run locally for the primary journey and dietary input MUST NOT be sent to a
cloud AI service. Model output MUST be grounded in retrieved recipes and known ingredients,
constrained to a documented schema, validated before display, and paired with a deterministic
fallback. The model MAY adapt and explain recipes; it MUST NOT bypass dietary exclusions,
nutrition validation, source attribution, or other product rules.

### IV. Evidence-Driven Retrieval
Search and ranking changes MUST be evaluated against representative pantry queries and explicit
relevance judgments. Retrieval, ingredient coverage, protein-target fit, dietary exclusion, and
adaptation validity MUST be tested independently so model quality cannot hide retrieval defects.
Claims in the submission write-up MUST be backed by recorded tests or user feedback.

### V. Small, Reviewable Increments
The project MUST proceed through approved specification, clarification, research, planning, task,
implementation, and convergence gates. Each implementation phase MUST produce an independently
testable user outcome. The simplest design that meets the approved requirements MUST be preferred;
new infrastructure, dependencies, and scope require a documented justification.

## Product and Safety Constraints

- The MVP MUST exclude beef, lamb, pork, and other red-meat ingredients from recommendations and
  adaptations.
- The MVP MUST prefer Indian meals while retaining useful global options.
- Users supply their own per-meal protein target; the product MUST NOT calculate a target from age,
  weight, health history, or activity.
- Recipe, image, and nutrition data MUST have documented reuse terms and required attribution.
- Ingredient and dietary input MUST remain on the local device during the primary journey.
- The primary flow MUST remain usable when the local model is unavailable, with adaptation clearly
  disabled rather than silently replaced by a cloud model.
- Accessibility basics—plain language, readable contrast, keyboard operation, and clear focus
  states—are release requirements, not optional polish.

## Development Workflow and Quality Gates

1. A PRD/specification MUST define user value, scope, acceptance scenarios, measurable outcomes,
   assumptions, and non-goals before technical planning.
2. Dataset selection MUST include a written audit of license, attribution, schema, cuisine coverage,
   red-meat filtering, nutrition completeness, and data quality.
3. Technical planning MUST record alternatives and explain every material dependency and original
   implementation decision.
4. Tasks MUST be grouped into independently demonstrable phases and traced to specification
   requirements.
5. Tests MUST be defined before implementation for nutrition calculations, dietary exclusions,
   retrieval relevance, model-output validation, API contracts, and the primary user journey.
6. Implementation MUST NOT begin until the user approves the specification and technical plan.
7. Each phase MUST pass its tests and a scope review before the next phase begins.
8. Final delivery MUST include a reproducible local setup, public code, a recorded demo, dataset
   attribution, and honest limitations.
9. Implementation work MUST occur on purpose-specific branches using prefixes such as `feat/`,
   `fix/`, `docs/`, or `chore/`; direct implementation commits to `main` are prohibited.
10. Each independently reviewable phase MUST be proposed through a pull request containing its
    scope, verification evidence, limitations, and linked specification tasks.
11. Pull requests MUST remain unmerged until the user reviews and approves them. Follow-up work MAY
    continue on a separate, non-dependent branch when doing so does not bypass the review gate.
12. Merges SHOULD use squash merge so `main` remains readable while GitHub retains branch, review,
    and pull-request history.
13. Coherent, testable progress MUST be recorded as iterative commits and pushed to its feature
    branch before the merge pull request is raised, so the development history remains reviewable.

## Governance
This constitution supersedes ad hoc implementation preferences and all downstream planning
artifacts. Amendments require a written rationale, user approval, a semantic version change, and a
review of affected specifications and plans. Every phase review MUST verify compliance; deviations
MUST be documented in the active plan with a reason and a remediation task. Major changes remove or
redefine a principle, minor changes add or materially expand governance, and patch changes clarify
without changing obligations.

**Version**: 1.1.0 | **Ratified**: 2026-10-03 | **Last Amended**: 2026-10-04
