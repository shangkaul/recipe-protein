# Plan: Local Recipe1M Search Index

## Decision

Keep Recipe1M JSON as source data and generate a local SQLite FTS5 database. LMDB was rejected for
search because it provides key/value lookup rather than a ranked inverted index. SQLite is already
available in Python, persists BM25 indexes, and can join recipe, image, and nutrition metadata.

## Data flow

1. Stream `layer1.json`; reject red meat and insert recipes plus FTS text.
2. Stream `layer2.json`; attach the first source image reference to indexed recipes.
3. Stream the nutrition subset; retain only plausible per-100g values and label their basis.
4. At runtime retrieve top FTS candidates, apply pantry/exclusion checks, and merge with UniTools.
5. Never use missing Recipe1M time, servings, cuisine, or nutrition as a generated value.

## Files

- `backend/scripts/build_recipe1m_index.py`: reproducible streaming builder.
- `backend/app/services/recipe1m.py`: optional runtime adapter.
- `backend/data/recipe1m.sqlite`: generated and ignored.
- `backend/tests/test_recipe1m.py`: fixture index and fallback tests.
