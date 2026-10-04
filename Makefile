.PHONY: setup setup-ai dev test build deploy deploy-down

setup:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements.txt
	npm install --prefix frontend

setup-ai:
	ollama pull gemma3:1b

dev:
	./scripts/dev.sh

test:
	backend/.venv/bin/pytest -q backend/tests
	npm run test --prefix frontend -- --run
	npm run lint --prefix frontend

build:
	npm run build --prefix frontend

deploy:
	docker compose up --build

deploy-down:
	docker compose down
