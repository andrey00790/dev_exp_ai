.PHONY: up down test healthcheck

up:
	docker compose up -d --build

down:
	docker compose down

test:
	python -m pytest -v

healthcheck:
	curl -f http://localhost:8000/health
