# Tasks: Local Pantry Intelligence and Recipe Adaptation

## Phase 1: Checkpoint 2 Foundation

- [ ] T001 Add optional exclusions input in `frontend/src/App.tsx`.
- [ ] T002 Apply normalized exclusions before ranking in `backend/app/services/catalog.py`.
- [ ] T003 Add Ollama client and loopback-only configuration in `backend/app/services/ollama.py`.
- [ ] T004 Add local model status to `GET /api/health` in `backend/app/api.py`.

## Phase 2: User Story 1 — Ambiguous Pantry Refinement

- [ ] T005 [US1] Add Pydantic refinement schema in `backend/app/models.py`.
- [ ] T006 [US1] Add bounded candidate generation in `backend/app/services/pantry_refinement.py`.
- [ ] T007 [US1] Call local structured output only for ambiguous terms.
- [ ] T008 [US1] Validate canonical IDs and merge without deleting deterministic terms.
- [ ] T009 [US1] Return parser provenance and fallback status from recipe search.
- [ ] T010 [US1] Show deterministic, refined, basic, and unresolved states in the PWA.
- [ ] T011 [US1] Add success, invalid-output, timeout, unavailable, and privacy tests.
- [ ] T012 [US1] Run mobile/desktop and Impeccable checks, then raise checkpoint PR.

## Phase 3: User Story 2 — Grounded Recipe Adaptation

- [ ] T013 [US2] Add adaptation proposal models and closed operation schema.
- [ ] T014 [US2] Add attributed local nutrient records and supported unit conversions.
- [ ] T015 [US2] Build grounded adaptation prompt from one source recipe and allowed operations.
- [ ] T016 [US2] Validate schema, canonical ingredients, exclusions, red meat, and quantities.
- [ ] T017 [US2] Apply changes and calculate deterministic nutrition deltas.
- [ ] T018 [US2] Add adaptation endpoint and actionable failure responses.
- [ ] T019 [US2] Build original-versus-adapted comparison in the recipe detail flow.
- [ ] T020 [US2] Add model, safety, nutrition, contract, and UI tests.
- [ ] T021 [US2] Run local end-to-end adaptation fixtures and raise checkpoint PR.

## Phase 4: Delivery Hardening

- [ ] T022 Run complete accessibility, privacy, performance, and offline checks.
- [ ] T023 Add deployment configuration without a cloud-model fallback.
- [ ] T024 Record demo evidence and document measured limitations.

## Dependencies

- T003–T004 block model-assisted work.
- T005–T011 complete User Story 1 and checkpoint 2 independently.
- T013–T021 begin only after checkpoint 2 merges.
- Search remains independently usable throughout every phase.

## Requirement Traceability

- T001–T002 → FR-006–FR-007 (free-text exclusions and hard filtering)
- T003–T004 → FR-016–FR-017 (local readiness and loopback-only inference)
- T005–T011 → FR-001–FR-005, FR-015–FR-017 (constrained refinement and fallback)
- T013–T021 → FR-008–FR-019 (grounded, validated adaptation and nutrition)
- T022–T024 → SC-001–SC-008 (release evidence and measurable outcomes)
