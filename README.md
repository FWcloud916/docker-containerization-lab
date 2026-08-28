# Docker Containerization Lab

The reproducible reference service for the Traditional Chinese article series
「Docker 與容器化工程：從原理、Dockerfile 到 Production 安全」.

The stack is deliberately small:

- Nginx is the only published entry point at `127.0.0.1:8080`.
- FastAPI exposes liveness, readiness, and a minimal item API.
- PostgreSQL is reachable only from the internal backend network.

## Dockerfile layer and cache baseline

The initial Dockerfile is intentionally cache-unfriendly: it copies the complete build context
before installing the Python project. The `dockerfile-layer-cache-optimization` checkpoint measures
why application-only changes therefore repeat dependency installation. Do not treat this tag as the
production image; a future checkpoint will replace it with the optimized multi-stage build.

## Run

```bash
cp .env.example .env
docker compose up --build --wait
curl http://127.0.0.1:8080/livez
curl http://127.0.0.1:8080/readyz
curl -X POST http://127.0.0.1:8080/items \
  -H 'content-type: application/json' \
  -d '{"name":"cache experiment"}'
curl http://127.0.0.1:8080/items
docker compose down --volumes
```

The password in `.env.example` is a disposable local-development placeholder. Never reuse it for a
real service or commit a populated `.env` file.

## Local checks

```bash
uv sync --frozen
uv run pytest
uv run ruff check
uv run ruff format --check
docker compose config --quiet
```

## Article checkpoints

`main` contains the latest lab. Each immutable checkpoint tag uses the corresponding article slug;
the first three articles predate this lab.

## License

MIT
