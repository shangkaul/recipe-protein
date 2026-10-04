#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x "backend/.venv/bin/flask" || ! -d "frontend/node_modules" ]]; then
  echo "Dependencies are missing. Run 'make setup' first."
  exit 1
fi

cleanup() {
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting Protein Pantry"
echo "  App: http://localhost:5173"
echo "  API: http://localhost:5001/api/health"

(
  cd backend
  .venv/bin/flask --app app run --debug --port 5001
) &
BACKEND_PID=$!

(
  cd frontend
  npm run dev -- --host 0.0.0.0
) &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
