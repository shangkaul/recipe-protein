# Implementation Plan: Protein Pantry Recommendations

**Branch**: `001-protein-pantry-recommendations` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

## Summary

Build Protein Pantry as a mobile-first React PWA backed by a local Flask API. The API loads the
audited UniTools recipe corpus, removes red-meat recipes, normalizes pantry language, and ranks
eligible meals with BM25 plus deterministic pantry/protein/time signals. A selected recipe can be
adapted by a local Ollama model within a closed schema; deterministic code validates every change
and calculates nutrition. The browse-first interface remains useful when search or model services
are unavailable.

## Technical Context

**Language/Version**: TypeScript 5.x, React 19, Python 3.13  
**Primary Dependencies**: Vite, vite-plugin-pwa, Lucide React, Flask, flask-cors, rank-bm25, Pydantic,
Requests  
**Storage**: Versioned JSON corpus and browser localStorage for last preferences; no database  
**Testing**: Vitest + Testing Library; pytest; Playwright mobile journey  
**Target Platform**: Installable mobile-first web app; local macOS/Linux Flask + Ollama host  
**Project Type**: React frontend + Flask API  
**Performance Goals**: 20–30 ranked results in under 3 seconds; responsive interactions under 100 ms  
**Constraints**: no cloud AI fallback, deterministic nutrition, red-meat hard exclusion, accessible
touch/keyboard UI, cached application shell  
**Scale/Scope**: one household, 501 bundled recipes, four principal views

## Constitution Check

- Parents-first browse and pantry journey: **PASS**
- Deterministic nutrition and visible provenance: **PASS**
- Grounded local AI with validation and failure fallback: **PASS**
- Retrieval fixtures and independent ranking tests: **PASS planned**
- Small demonstrable phases: **PASS**
- Dataset audit and license documentation: **PASS**
- Specification and plan approval: **PASS** — user authorized implementation on 2026-10-04

## Architecture

1. **Corpus loader** converts UniTools records into internal recipe models and applies conservative
   red-meat exclusion before indexing.
2. **Pantry parser** tokenizes natural language and resolves a curated synonym map. Deterministic
   parsing remains the fast fallback; local Gemma may refine ambiguous terms and core-versus-basic
   roles through a closed JSON schema whose canonical IDs are validated against the corpus.
3. **Ranking service** uses BM25 for lexical relevance, then combines coverage, nutrition-target,
   time, and cuisine signals with an explanation payload.
4. **Adaptation service** calls local Ollama for schema-bound changes, validates ingredients and
   constraints, and applies deterministic nutrition deltas.
5. **Flask API** exposes health, featured, search, recipe detail, and adaptation endpoints.
6. **React PWA** provides browse, search, result detail, and adaptation views with install/offline
   states and local preference persistence.

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   ├── models/
│   └── services/
├── data/
└── tests/
frontend/
├── public/
└── src/
    ├── components/
    ├── hooks/
    ├── services/
    └── types/
specs/001-protein-pantry-recommendations/
└── contracts/
```

**Structure Decision**: Separate frontend and backend keep the installable client independent from
the local data/model process while preserving a small, explicit API boundary.

## Phases

1. Searchable foundation: corpus ingestion, exclusions, parser, ranking, API, and tests.
2. Mobile PWA: browse-first shell, pantry search, results, recipe detail, offline/API states.
3. Grounded adaptation: Ollama schema, validation, deterministic nutrition deltas, UI comparison.
4. Hardening: full journey tests, accessibility, PWA audit, documentation, demo readiness.

## Complexity Tracking

No constitution violations. The two-process architecture is required because local model and BM25
work belong outside the browser while the PWA must remain installable and responsive.
