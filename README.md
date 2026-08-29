# Docker Containerization Lab

The reproducible reference service for the Traditional Chinese article series
「Docker 與容器化工程：從原理、Dockerfile 到 Production 安全」.

The stack is deliberately small:

- Nginx is the only published entry point at `127.0.0.1:8080`.
- FastAPI exposes liveness, readiness, and a minimal item API.
- PostgreSQL is reachable only from the internal backend network.

## Production multi-stage checkpoint

`main` now uses a production-oriented, digest-pinned, multi-stage Dockerfile. Dependencies are
resolved in a builder stage, BuildKit keeps downloaded artifacts in a cache mount, and the runtime
stage receives only the virtual environment and application package. It runs as UID/GID `10001`
instead of root.

The `variants/` directory keeps two runtime alternatives and one experimental control:

- `Dockerfile.alpine` uses musl-based Alpine and the same non-root boundary.
- `Dockerfile.distroless` uses the distroless Debian 13 Python `nonroot` image and has no shell.
- `Dockerfile.slim-no-cache-mount` removes only the cache mount, so lockfile invalidation can be
  compared without changing the rest of the build.

See [`evidence/production-multistage-dockerfile.md`](evidence/production-multistage-dockerfile.md)
for the exact environment, commands, measured timings, image sizes, and runtime checks.

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

Use an override to run another runtime with the same proxy, database, health checks, and API test:

```bash
docker compose -f compose.yaml -f variants/compose.alpine.yaml up --build --wait
docker compose -f compose.yaml -f variants/compose.distroless.yaml up --build --wait
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
docker compose -f compose.yaml -f variants/compose.alpine.yaml config --quiet
docker compose -f compose.yaml -f variants/compose.distroless.yaml config --quiet
```

## Article checkpoints

`main` contains the latest lab. Each immutable checkpoint tag uses the corresponding article slug;
the first three articles predate this lab. The intentionally cache-unfriendly predecessor is kept at
`dockerfile-layer-cache-optimization`; this production version is
`production-multistage-dockerfile`.

## License

MIT
