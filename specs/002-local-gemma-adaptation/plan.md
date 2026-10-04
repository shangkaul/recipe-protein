# Implementation Plan: Local Pantry Intelligence and Recipe Adaptation

**Branch**: `feat/local-gemma-adaptation` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

## Summary

Extend Protein Pantry with optional free-text exclusions and a local open-weight model accessed
through Ollama. Deterministic parsing remains first and sufficient for ordinary searches. Only
unresolved or ambiguous pantry terms are sent to the local model, whose structured output is
validated against the current ingredient vocabulary before retrieval. A later phase uses the same
local boundary to propose constrained changes to one selected recipe; safety and deterministic
nutrition validation remain authoritative.

## Technical Context

**Language/Version**: Python 3.13, TypeScript 6, React 19  
**Primary Dependencies**: Flask, Pydantic, Requests, Ollama local HTTP API, React  
**Storage**: Existing JSON corpus plus a versioned local attributed nutrition table; no database  
**Testing**: pytest with mocked Ollama responses; Vitest and Testing Library; manual local-model fixtures  
**Target Platform**: Mobile-first PWA with a household-local Flask/Ollama host  
**Project Type**: Existing React frontend plus Flask API  
**Performance Goals**: deterministic search under 3 seconds; refinement under 10 seconds;
adaptation under 30 seconds on the demonstration Mac  
**Constraints**: no cloud inference, no generated nutrition, closed schemas, automatic red-meat
exclusion, original recipe always retained  
**Scale/Scope**: one household, one active request, 501 bundled recipes, Gemma 3 1B default

## Constitution Check

- Parents-first value: **PASS** — inference is limited to confusing input and one chosen recipe.
- Deterministic nutrition: **PASS** — model schemas contain no trusted nutrition fields.
- Grounded local AI: **PASS** — localhost-only Ollama, known IDs, schema and safety validation.
- Evidence-driven retrieval: **PASS** — deterministic and refined parses are independently tested.
- Small reviewable increments: **PASS** — refinement and adaptation are separate PR checkpoints.
- Branch and PR gates: **PASS** — all work remains on `feat/local-gemma-adaptation` until approval.

## Architecture

1. `OllamaClient` owns localhost status checks and structured chat calls with bounded timeouts.
2. `PantryRefinementService` receives only raw text, deterministic parse, and a bounded canonical
   candidate list; it validates returned IDs and merges accepted refinements without deleting
   deterministic terms.
3. Search returns parser provenance and model status so the UI can explain fallback behavior.
4. `AdaptationService` later provides one source recipe and a closed operation list to the model,
   validates the proposal, applies changes, and delegates nutrition deltas to deterministic code.
5. API errors distinguish model unavailable, timeout, invalid output, and rejected proposal without
   exposing raw prompts or stack traces.

## Project Structure

```text
backend/app/
├── api.py
├── models.py
└── services/
    ├── ollama.py
    ├── pantry_refinement.py
    ├── adaptation.py
    ├── nutrition.py
    └── validation.py
backend/data/
└── nutrient-reference.json
backend/tests/
├── test_pantry_refinement.py
├── test_adaptation.py
└── test_nutrition.py
frontend/src/
├── components/
│   └── AdaptationView.tsx
├── services/api.ts
└── types/recipe.ts
```

**Structure Decision**: Keep model calls behind backend services so no browser path can silently
contact a remote model and every output passes the same validation boundary.

## Phases

1. **Checkpoint 2**: exclusions, Ollama status, schema-bound ambiguous pantry refinement, fallback,
   provenance UI, tests, and PR.
2. **Checkpoint 3**: adaptation proposal, validation, deterministic nutrition deltas, comparison UI,
   and PR.
3. **Checkpoint 4**: end-to-end hardening, deployment, demo, and submission evidence.

## Complexity Tracking

No constitution violations. The local model service is isolated because model availability and
malformed output are expected runtime states, not exceptional search failures.
