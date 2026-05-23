# PSL Backend — Project Solo Levelling

Real-life RPG self-improvement backend. FastAPI + Postgres + Redis.

See `docs/PRD.md` and `docs/TDD.md` for product and technical specs.

## Stack

- Python 3.12 + uv
- FastAPI, structlog, pydantic-settings
- SQLAlchemy 2.0 async + Alembic + asyncpg (PR2+)
- Redis (rate limit + cache, PR3+)
- argon2 + JWT cookies + CSRF (PR3+)
- SQLAdmin (PR6+)
- pytest + testcontainers-postgres (PR7+)

## Quickstart

```bash
# 1. Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Bootstrap project
uv sync

# 3. Copy env
cp .env.example .env

# 4. Start infra + app
docker compose up -d

# 5. Health check
curl http://localhost:8000/healthz
```

## Local dev (app on host)

```bash
docker compose up -d postgres redis
uv run uvicorn app.main:app --reload
```

## Quality

```bash
uv run ruff check .
uv run ruff format .
uv run mypy app
uv run pre-commit install
```

## Tests

```bash
# Option A (default): testcontainers spins up disposable Postgres + Redis
uv run pytest -q

# Option B: reuse running compose Postgres + Redis (faster; needs psl_test DB)
docker compose exec postgres psql -U psl -d psl -c "CREATE DATABASE psl_test;"
TEST_DATABASE_URL="postgresql+asyncpg://psl:psl@localhost:5432/psl_test" \
TEST_REDIS_URL="redis://localhost:6379/1" \
  uv run pytest -q
```

## Layout

```
app/
  main.py             # FastAPI app + lifespan
  core/               # config, db, redis, security, logging, dependencies
  routers/            # HTTP routes (per resource)
  services/           # business logic
  repositories/       # data access
  models/             # SQLAlchemy ORM models
  schemas/            # pydantic request/response
  migrations/         # alembic
  tests/              # pytest
docs/
docker-compose.yml
Dockerfile
pyproject.toml
```

## Branching

Stacked PRs per feature. Each branch on top of the previous:
`main` → `chore/scaffold` → `feat/db-core` → `feat/auth` → `feat/stats` → `feat/activities` → `feat/admin` → `feat/tests`.
