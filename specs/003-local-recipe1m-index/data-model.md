# Data Model: Private Recipe1M Index

## SQLite tables

### `recipes`

One safe Recipe1M record per row. The original ten-character ID is unique. Titles, source URLs,
partition names, ingredient text, and instruction text are retained. Image ID/URL and validated
per-100g protein, energy, and fat are nullable.

### `recipe_fts`

An external-content FTS5 table linked to `recipes.rowid`. Recipe ID is unindexed; title,
ingredients, and instructions are indexed with title and ingredient fields weighted above method
text during BM25 retrieval.

### `metadata`

Build schema version, source/safe/excluded counts, attached image and nutrition counts, and a
`complete=1` marker. Runtime search refuses partial builds without the completion marker.

## Privacy and licensing boundaries

- Raw JSON, generated SQLite files and sidecars, and downloaded images remain local and ignored.
- No Recipe1M content is included in application commits, build artifacts, or deployment images.
- Recipe source URLs remain attached to records; the UI identifies the local Recipe1M corpus.
- The application makes no blanket license claim for source recipes or images. Original source
  terms apply, and source image URLs are cached only on the user's device.
- Recipe1M nutrition is optional source data labelled per 100g. It is never converted to or shown
  as per-serving nutrition without a deterministic serving calculation.

## Runtime lifecycle

The builder writes to `recipe1m.sqlite.building`, commits a completion marker, optimizes and
vacuums the database, then atomically replaces the target. The Flask adapter opens completed
indexes read-only and falls back to the bundled UniTools corpus when the index is absent or invalid.
