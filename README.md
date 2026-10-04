# Protein Pantry

Protein Pantry is a mobile-first PWA that helps a household browse familiar, higher-protein meals
and find recipes that fit ingredients already in the kitchen. Users choose their own per-meal
protein target; the app ranks grounded recipes and explains pantry fit without prescribing medical
or dietary targets.

## Why it exists

Choosing dinner should not require comparing dozens of recipe pages or sending dietary information
to a cloud AI service. Protein Pantry is designed for the creator's parents: browse an appealing
meal first, then narrow the choices with a natural-language pantry description, preferred cooking time, and
a practical protein target.

## Current features

- Browse-first meal ideas with Indian recipes preferred when relevant
- Natural-language pantry input with common Indian English ingredient aliases
- Optional local Gemma refinement for unresolved or misspelled pantry words
- Optional free-text ingredient exclusions, with automatic red-meat exclusion always active
- BM25 retrieval combined with pantry coverage, protein-target fit, cooking time, and cuisine
- Hard exclusion of beef, pork, lamb, other red meat, and red-meat-derived ingredients
- Per-serving protein, calories, time, ingredients, instructions, and source attribution
- Mobile-first responsive interface with installable PWA metadata and cached application shell
- Structured model output is validated against the bundled ingredient vocabulary before retrieval
- Search remains useful when Gemma or Ollama is unavailable
- Optional private Recipe1M SQLite/FTS5 index for broader local recipe coverage
- No account, health profile, or cloud AI fallback

Grounded selected-recipe adaptation and deterministic post-adaptation nutrition calculation are
planned in the next checkpoint. Model-generated nutrition will never be displayed.

## Architecture

```text
React + TypeScript PWA
        │
        ▼
Local Flask API
  ├── pantry normalization
  ├── schema-validated local Gemma refinement
  ├── red-meat safety filter
  ├── BM25 retrieval and deterministic ranking
  ├── versioned public recipe corpus
  └── optional local Recipe1M FTS5 index
        │
        └── grounded local Ollama adaptation (next checkpoint)
```

The frontend and API run locally. Pantry text, exclusions, and protein targets are not sent to a
cloud model.

## Recipe data

The bundled MVP corpus is **UniTools World Recipes v2**:

- 501 recipes from 127 countries
- serving counts, structured quantities, instructions, cooking time, protein, and calories
- dataset license: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- source and attribution: [UniTools](https://theunitools.com/en/data)

Each displayed photo retains its own author and license metadata. The API applies a conservative
red-meat exclusion before recipes enter the search index. Full attribution is documented in
[`backend/data/ATTRIBUTION.md`](backend/data/ATTRIBUTION.md).

### Optional local Recipe1M index

Recipe1M source data is not bundled or deployed. If you have a local copy, build a private SQLite
index from the repository root:

```bash
backend/.venv/bin/python backend/scripts/build_recipe1m_index.py \
  --layer1 /path/to/layer1.json \
  --layer2 /path/to/layer2.json \
  --nutrition /path/to/recipes_with_nutritional_info.json
```

The generated `backend/data/recipe1m.sqlite` and on-demand image cache are ignored by Git. Set
`RECIPE1M_DB_PATH` or `RECIPE1M_IMAGE_CACHE` to use other local paths. Recipe1M records do not
provide reliable serving counts or cooking times, so those fields remain unavailable. Its optional
nutrition subset is labelled per 100g and is never presented as per-serving nutrition.

## Run locally

### Requirements

- Node.js 22+
- Python 3.11+
- Ollama when using optional local pantry refinement or the upcoming adaptation feature

### Fastest setup

No environment needs to be activated first. From the repository root:

```bash
make setup
make setup-ai  # optional: downloads gemma3:1b through Ollama
make dev
```

`make setup` creates `backend/.venv`, installs the Python packages inside it, and installs the
frontend packages. `make dev` uses that environment directly and starts both services. Press
`Control+C` once to stop them. `make setup-ai` is deliberately separate: ordinary search works
without downloading a model. When installed, Gemma receives only unresolved pantry input through
Ollama's loopback API; invalid, timed-out, and unavailable responses fall back to direct matches.

### Manual setup

If you prefer separate terminals, start the API:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug --port 5001
```

### 2. Start the PWA

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` requests to the Flask
service on port `5001`.

## Tests

```bash
cd backend && .venv/bin/pytest
cd frontend && npm run test -- --run
cd frontend && npm run build
cd frontend && npm run lint
```

## Planning and product decisions

This project uses GitHub Spec Kit. The approved specification, dataset audit, architecture, API
contract, and phased task list are in
[`specs/001-protein-pantry-recommendations/`](specs/001-protein-pantry-recommendations/).
The local model feature has its own Spec Kit packet in
[`specs/002-local-gemma-adaptation/`](specs/002-local-gemma-adaptation/).
The private Recipe1M index is specified in
[`specs/003-local-recipe1m-index/`](specs/003-local-recipe1m-index/).

Important guarantees are captured in the
[`project constitution`](.specify/memory/constitution.md): deterministic nutrition, grounded local
AI, evidence-driven retrieval, explicit dietary exclusions, and small reviewable increments.

## Contributing

All implementation work uses feature branches and pull requests. Pull requests remain unmerged
until the project owner approves them. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the workflow and
quality gates.

## License

Application code is available under the [MIT License](LICENSE). Recipe data and recipe photos retain
their separately documented source licenses and attribution requirements.
