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
```
