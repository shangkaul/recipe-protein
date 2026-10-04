# Quickstart

## Requirements

- Node.js 22+
- Python 3.11+
- Ollama (only required for adaptation)

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug --port 5001
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. To test from a phone, run Vite with `--host`, expose Flask on the
local network, and set `VITE_API_URL` to the computer's LAN address.

## Local adaptation

```bash
ollama pull gemma3:1b
OLLAMA_MODEL=gemma3:1b flask --app app run --debug --port 5001
```

If Ollama or the model is unavailable, Protein Pantry still supports browse, search, comparison,
and recipe details. It never sends the request to a cloud model.

## Tests

```bash
cd backend && pytest
cd frontend && npm test -- --run
cd frontend && npm run build
```
