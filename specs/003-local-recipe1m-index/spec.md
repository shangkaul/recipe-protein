# Feature Specification: Local Recipe1M Search Index

**Branch**: `feat/local-recipe1m-index`  
**Created**: 2026-10-04  
**Status**: Approved — implementation authorized 2026-10-04

## Goal

Use the user's local Recipe1M download to improve recipe coverage, especially pasta, without
committing, redistributing, or deploying the dataset. UniTools remains the public fallback.

## Requirements

- **FR-001**: Build a persistent local full-text index without loading 1.3 GB JSON on app startup.
- **FR-002**: Source JSON, generated indexes, and cached images MUST remain ignored by Git.
- **FR-003**: Red-meat recipes MUST be excluded while building and querying the index.
- **FR-004**: Pantry and exclusion filters MUST remain authoritative after full-text retrieval.
- **FR-005**: Missing servings, time, cuisine, images, or nutrition MUST be shown honestly.
- **FR-006**: Recipe1M nutrition MUST NOT be presented as per-serving nutrition.
- **FR-007**: Source recipe URLs and local-corpus provenance MUST remain visible.
- **FR-008**: `layer2.json` image references MAY be used locally with graceful broken-image fallback.
- **FR-009**: The application MUST work unchanged when no local Recipe1M index exists.

## Acceptance Scenarios

1. Searching `pasta` returns safe pasta recipes from the local index.
2. Searching with a red-meat exclusion never returns red-meat recipes.
3. A record without nutrition or time displays “not listed,” not a generated value.
4. Removing the SQLite index restores UniTools-only behavior without an application error.

## Success Criteria

- Index all safe Recipe1M records in a reproducible streaming build.
- Return the first local candidates in under one second on the demonstration Mac.
- Keep repository size unchanged apart from index code and documentation.
