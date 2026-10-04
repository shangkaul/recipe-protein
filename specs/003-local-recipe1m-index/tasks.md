# Tasks: Local Recipe1M Search Index

- [x] T001 Add ignored local index and image-cache paths.
- [x] T002 Implement streaming JSON-array reader and SQLite FTS5 builder.
- [x] T003 Filter red meat and validate optional per-100g nutrition during import.
- [x] T004 Attach `layer2.json` image references and source recipe URLs.
- [x] T005 Add optional runtime Recipe1M search/detail adapter.
- [x] T006 Merge local candidates with UniTools while preserving pantry-first ranking.
- [x] T007 Show unavailable time/nutrition honestly in search and detail UI.
- [x] T008 Add fixture, fallback, exclusion, pasta, and detail tests.
- [x] T009 Build the local full index and record performance/count evidence.
- [x] T010 Run full validation and raise the checkpoint PR.
- [ ] T011 Add deterministic Recipe1M protein/calorie calculation from parsed ingredient quantities
  and an attributed nutrient reference. Local Gemma may propose structured quantity/yield extraction,
  but deterministic validation remains authoritative. Use an explicit source yield when present;
  otherwise require user-confirmed servings before displaying per-serving values.

## Full-index evidence

- Source records scanned: 1,029,720
- Safe indexed records: 818,408
- Red-meat/invalid records excluded: 211,312
- Records with image metadata: 323,090
- Records with plausible per-100g nutrition: 47,518
- Build time: 98.14 seconds
- Index size: 1,635,311,616 bytes
- 160-candidate FTS latency: 55.6–239.2 ms across representative local queries
