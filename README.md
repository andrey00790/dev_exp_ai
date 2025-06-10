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

## LLM Configuration

The language model client is selected via environment variables:

* `MODEL_MODE` – `local` to use Ollama or `openai` for the OpenAI API.
* `MODEL_URL` – base URL of the Ollama HTTP API when using local mode.
* `MODEL_NAME` – model name for the local Ollama service.
* `OPENAI_API_KEY` – API key for OpenAI requests.
* `OPENAI_MODEL` – OpenAI model identifier.

Example usage:

```python
from llm.llm_loader import load_llm

llm = load_llm()
text = await llm.generate("Hello world")
```
