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
- Progress-preserving pantry search: current meals remain visible while replacements are ranked
- User-triggered local Gemma adaptation of one selected, attributed source recipe
- Deterministic adaptation nutrition from a local USDA FoodData Central reference
- User-confirmed serving yield before Recipe1M per-serving nutrition is displayed
- Optional “Verified nutrition only” search with availability labels before recipe selection
- No account, health profile, or cloud AI fallback

Gemma proposes only bounded ingredient operations and method notes. Python validates pantry fit,
exclusions, red-meat safety, quantities, and nutrition before an adaptation is displayed. Model-
generated nutrition and model-guessed serving counts are never accepted.

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
  ├── optional local Recipe1M FTS5 index
  ├── closed-schema local Gemma adaptation
  ├── deterministic USDA-backed nutrition validation
  └── grounded local Ollama adaptation
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

When ingredient-level Recipe1M nutrition passes import validation, the detail view can calculate
per-serving values after the user confirms how many servings the recipe will make. Recipes outside
that validated subset continue to show nutrition as unavailable.

Two independent guards keep a wrong number off the screen. Import validation rejects batch-scale
records, energy-dense values, and protein that exceeds the mass of food it is measured in.
Serving-time validation then refuses any result that is not a plausible portion of food, so a
recipe whose yield was mis-parsed can never divide into an impossible serving.

Because some valid totals only become a credible portion at a higher serving count, each recipe
carries the smallest serving count that produces one. A card is labelled **Verified nutrition** only
when such a count exists, and the detail view states the floor instead of dead-ending: if you enter
fewer servings, the field is corrected and the reason is explained.

Only 17,200 of the 818,408 safe records in the current private Recipe1M index have fully validated
ingredient-level nutrition. Turn on **Verified nutrition only** during pantry search to query that
subset directly. Pantry fit remains the primary ranking signal; nutrition availability is clearly
labelled before a recipe is opened.

### Grounded local adaptation

After searching a pantry and opening a recipe, choose **Adapt using my pantry**. For Recipe1M
recipes, confirm the serving yield first. Gemma runs through the configured loopback-only Ollama
service and may propose one to three additions or increases from the supported pantry ingredients.
Unknown, excluded, unsafe, non-pantry, excessive, unverifiable, or nutritionally insignificant
changes are rejected. A proposal that would not move protein by a meaningful amount fails closed
rather than presenting a cosmetic difference.

Protein, calories, and fat deltas are calculated in Python from the bundled compact reference in
`backend/data/nutrient-reference.json`. Those records retain their USDA FoodData Central IDs,
descriptions, per-100g basis, retrieval date, and public-domain provenance. The application makes no
runtime requests to USDA, and the model never supplies nutrient values.

## Run locally

### Requirements

- Node.js 22+
- Python 3.11+
- Ollama when using optional local pantry refinement or recipe adaptation

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

### Local production deployment

Docker Compose serves the built PWA at `http://127.0.0.1:8080`, runs Flask with Gunicorn, and keeps
Ollama and Gemma inside the local Docker network namespace. It does not configure or fall back to a
cloud model.

```bash
make deploy
```

The first run downloads the configured Ollama image and `gemma3:1b`. Set `APP_PORT`, `OLLAMA_MODEL`,
or `OLLAMA_IMAGE` before starting to override those defaults. `backend/data` is mounted locally so
an ignored Recipe1M index remains private and is never copied into an image. Stop the stack with
`make deploy-down`.

Search and the bundled UniTools corpus remain usable when Ollama is unavailable; only local model
refinement and adaptation are disabled.

## Measured limitations

- Recipe1M does not provide reliable servings or cooking times.
- 17,200 of 818,408 safe local Recipe1M records pass ingredient-nutrition validation for
  serving-based calculations. The earlier figure of 47,047 came from validation that checked only
  ratios, which admitted catering-batch records; absolute scale limits are now enforced too.
- Adaptation supports a compact set of pantry proteins with locally stored USDA records.
- The local model chooses which pantry ingredients to change and why. It does not choose the
  grams: the host solves each quantity from the verified nutrient records, and refuses a boost
  that would stop being recognisably the source recipe.
- Nutrition is approximate cooking guidance, not medical advice.
- The PWA shell and saved featured meals work offline; new pantry searches require the local API.

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
Deterministic nutrition and grounded adaptation are specified in
[`specs/004-nutrition-adaptation/`](specs/004-nutrition-adaptation/).

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
