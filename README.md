# AI Assistant MVP

This project is a minimal FastAPI service used for development experiments.

## Setup

```bash
make up       # build and start the service
make healthcheck  # verify that /health returns a 200
make test     # run tests
make down     # stop containers
```

The `/health` endpoint should respond with:

```json
{"status": "ok"}

Basic infrastructure with FastAPI service, Qdrant, PostgreSQL and Ollama containers.

## Setup

1. Copy `.env.example` to `.env.local` and adjust variables if needed.
2. Start services (uses Docker if available or runs locally):

```bash
make up
```

For local development without Docker:

```bash
make run
```

3. Check service health:

```bash
make healthcheck
```

4. Run tests:

```bash
make test
```

5. Stop services (no-op if running locally):

```bash
make down
```
