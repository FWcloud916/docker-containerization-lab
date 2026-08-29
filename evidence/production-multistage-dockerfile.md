# Production multi-stage Dockerfile evidence

This checkpoint supports the article `production-multistage-dockerfile`. Results are local
observations, not universal benchmarks.

## Environment

- Date: 2026-08-30
- Host architecture: Apple Silicon / arm64
- Docker client: 29.6.2
- Docker Engine: 29.2.1
- Docker API: 1.53
- Docker Buildx: 0.35.0
- BuildKit driver: isolated `docker-container`
- VM: Colima, Ubuntu 24.04.4 LTS, overlayfs
- Python dependency tool: uv 0.11.25

## Inputs pinned for the experiment

| Variant | Builder/runtime input |
|---|---|
| Debian slim | `python:3.13-slim@sha256:7ce4b6dfe35e55397b7cda544f8a13f191b7ae28dc5aad71fe664dbc9bc2623f` |
| Alpine | `python:3.13-alpine@sha256:540c7d91f98ff6880174c40e99067bf5941eb54d818a7a5e094d188b196a934d` |
| Distroless builder | `python:3.13-slim-trixie` at the same slim digest |
| Distroless runtime | `gcr.io/distroless/python3-debian13:nonroot@sha256:f3d5ddc6c64a019fe520e7f005f2880be21e6afc461b10a3c15ef2e4edc71e33` |

These digests are evidence anchors for this checkpoint. They must still be refreshed deliberately
when upstream security fixes are adopted.

## Build cache experiment

The isolated builder was created with:

```bash
docker buildx create \
  --name production-multistage-lab \
  --driver docker-container \
  --bootstrap
```

The slim build command was:

```bash
/usr/bin/time -p docker buildx build \
  --builder production-multistage-lab \
  --progress=plain \
  --load \
  -t docker-containerization-lab-api:slim .
```

| Case | Total time | Dependency step | Observation |
|---|---:|---:|---|
| First isolated slim build | 54.99 s | 16.4 s | Includes base and frontend downloads into the new builder |
| Identical warm build | 2.46 s | cached | Every builder and runtime filesystem step was `CACHED` |
| Source-only change | 2.06 s | cached | Only `COPY app /app/app` ran again |
| Lockfile byte change, cache mount | 3.53 s | 0.8 s | Dependency layer ran; 15 packages reused without download |
| First no-cache-mount control | 8.94 s | 5.1 s | Downloaded the two platform-specific binary wheels |
| Lockfile byte change, no cache mount | 7.43 s | 3.4 s | Downloaded those binary wheels again |

The lockfile change was a temporary TOML comment, so the dependency graph did not change. The file
was restored after each run. The source-only change was also restored. This separates layer-cache
invalidation from package-cache reuse: the dependency `RUN` must execute after a lockfile change,
but a cache mount can prevent the execution from repeating network downloads.

The first-build totals are sensitive to network speed and which base layers the builder already has.
The useful evidence is which steps rerun, plus the cache-mount/no-cache-mount behavior under the same
lockfile-only invalidation.

## Runtime results

Images were inspected with `docker image inspect`; file boundaries were inspected by overriding the
entrypoint with the image's virtual-environment Python.

| Runtime | Local image size | UID | Python | Shell | `uv` | Build metadata in `/app` |
|---|---:|---:|---|---|---|---|
| Debian slim | 55,854,805 B | 10001 | 3.13.15 | `/usr/bin/sh` | absent | absent |
| Alpine | 27,837,435 B | 10001 | 3.13.15 | `/bin/sh` | absent | absent |
| Distroless | 35,173,070 B | 65532 | 3.13.5 | absent | absent | absent |

For all three images, `/app/app` existed while `/app/uv.lock`, `/app/pyproject.toml`, and
`/app/tests` did not. The distroless builder deliberately creates `/usr/bin/python` before creating
the virtual environment because that is the interpreter path in the runtime image. Builder and
runtime are both Python 3.13 on Debian 13; patch versions need not be byte-for-byte identical, but
the copied native dependencies must be tested in the final runtime.

## End-to-end validation

Each runtime was started with the same Nginx and PostgreSQL services. Compose reported all three
services healthy. For every variant, these requests succeeded through the published Nginx endpoint:

```text
GET  /livez  -> {"status":"live"}
GET  /readyz -> {"status":"ready"}
POST /items  -> created id 1
GET  /items  -> returned the created item
```

The disposable Compose volume was removed after each variant.
