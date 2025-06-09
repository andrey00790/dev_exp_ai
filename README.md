# AI Assistant MVP

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
