# Quickstart: Local Gemma Features

## Prerequisites

Complete the root `make setup`, then install and start Ollama.

```bash
ollama pull gemma3:1b
ollama list
make dev
```

Open `http://localhost:5173`. The app should report the local model as ready.

## Validation scenarios

### Deterministic search

Search `chicken, rice, bread, oregano and other spices`. Expected: chicken/rice/bread are core,
oregano/spices are basic, and no model is required.

### Local refinement

Search a fixture containing an unresolved spelling or mixed-language alias. Expected: validated
canonical terms are marked as locally refined; unknown returned IDs are not accepted.

### Fallback

Stop Ollama and repeat the ambiguous search. Expected: search succeeds with deterministic terms,
unresolved terms remain visible, and the app shows a local-model unavailable message.

### Exclusions

Enter `peanuts, coconut` under Avoid ingredients. Expected: matching recipes do not appear.

### Adaptation (Checkpoint 3)

Open one recipe and request adaptation. Expected: explicit changes, validated ingredients and
quantities, deterministic nutrition, source attribution, and a clear failure when unsupported.

## Automated verification

```bash
make test
make build
```
