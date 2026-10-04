.PHONY: setup dev test build

setup:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements.txt
	npm install --prefix frontend

dev:
	./scripts/dev.sh

test:
	backend/.venv/bin/pytest -q backend/tests
	npm run test --prefix frontend -- --run
	npm run lint --prefix frontend

build:
	npm run build --prefix frontend
