.PHONY: up down test healthcheck

up:
	docker compose up -d --build

down:
	docker compose down

test:
	python -m pytest -v

healthcheck:
	curl -f http://localhost:8000/health

.PHONY: up down healthcheck test run

docker_available := $(shell command -v docker 2>/dev/null)

up:
	@if [ -n "$(docker_available)" ]; then \
	docker compose up -d; \
	else \
	nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 & echo $$! > .app.pid; \
fi

down:
	@if [ -n "$(docker_available)" ]; then \
	docker compose down; \
	else \
	[ -f .app.pid ] && kill $$(cat .app.pid) && rm .app.pid || echo "Nothing to stop"; \
fi

healthcheck:
		@if ! curl -fs http://localhost:8000/health >/dev/null 2>&1; then \
			echo "Starting app for healthcheck"; \
			uvicorn app.main:app --host 0.0.0.0 --port 8000 & \
			pid=$$!; \
			sleep 2; \
			curl -f http://localhost:8000/health; \
			kill $$pid; \
		else \
			curl -f http://localhost:8000/health; \
	fi

test:
			pytest -v --cov=app --cov-report=term-missing --cov-fail-under=80

run:
			uvicorn app.main:app --host 0.0.0.0 --port 8000
