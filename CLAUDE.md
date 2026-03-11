# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from `backend/` directory unless noted otherwise.

```bash
# Dev environment (hot reload, all services)
docker compose -f docker-compose.dev.yml up --build

# Tests
pytest
pytest tests/test_sources.py          # single test file
pytest -k "test_create" -v            # by name pattern
pytest --cov=app                      # with coverage

# Lint & format
ruff check .
ruff format .
mypy app                               # strict type checking

# Migrations (run inside container or with local venv)
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Celery worker (dev)
uv run celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

## Architecture

This is a FastAPI + Celery distributed system. The API handles HTTP, while CPU-intensive work (PDF processing, video generation) runs in Celery workers via RabbitMQ.

```
API Service (FastAPI, port 8000)
  └─ async requests → RabbitMQ → Celery Worker
                                    ├─ process_source: PDF → embeddings → pgvector
                                    └─ generate_video: Gemini TTS → MoviePy → MP4

Database: PostgreSQL 16 + pgvector extension
  ├─ API uses: AsyncSession (asyncpg driver)
  └─ Workers use: SyncSessionLocal (psycopg2, Celery requirement)
```

**External services**: Google Gemini API (LLM: `gemini-2.5-flash-lite`, embeddings: `gemini-embedding-001`, TTS for video). Optional LangSmith tracing.

## Key Patterns

**Feature layout** — each feature has four files:
- `api/v1/endpoints/{feature}.py` — HTTP handlers only
- `models/{feature}.py` — SQLAlchemy ORM model
- `schemas/{feature}.py` — Pydantic request/response schemas
- `services/{feature}_service.py` — all business logic

**Shared dependencies**:
```python
DbSession = Annotated[AsyncSession, Depends(get_db)]      # app/api/deps.py
CurrentUser = Annotated[User, Depends(get_current_user)]
```

**Adding a new feature**:
1. Create model → schema → service → endpoint files
2. Import router in `app/api/v1/router.py` and call `api_router.include_router(...)`
3. Generate migration: `alembic revision --autogenerate -m "..."`

**Background tasks**: Enqueue via `task.delay(...)` from endpoints; workers update DB status (`pending → processing → ready/failed`). Celery tasks retry 3× with 60s backoff.

**Custom exceptions** (from `app/core/exceptions.py`): `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `ConflictError`, `UnprocessableError`.

**Settings**: `from app.core.config import settings` — pydantic-settings singleton with `@lru_cache`. Required env vars: `SECRET_KEY`, `POSTGRES_PASSWORD`, `GEMINI_API_KEY`.

**Vector storage**: PGVector collections namespaced as `source_{source_id}`. Tables: `langchain_pg_collection`, `langchain_pg_embedding`.

**File uploads**: Stored at `{UPLOAD_DIR}/{notebook_id}/{source_id}/{filename}`. Default upload dir: `/app/uploads`.

## Auth

JWT (HS256, 30-min expiry). Endpoints needing auth inject `CurrentUser`. Ownership is verified via notebook joins in service layer (not endpoints).

## Tooling Config

- **Ruff**: selects E/F/I/N/W/UP, line length 88, ignores E501
- **MyPy**: strict, py3.12
- **Pytest**: `asyncio_mode="auto"`, testpaths=`["tests"]`
- **Package manager**: `uv` (pyproject.toml)
