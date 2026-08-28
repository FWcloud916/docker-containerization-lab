# Dockerfile layer and cache checkpoint

Verification date: 2026-08-28 (Asia/Taipei)

## Environment

- Host architecture: arm64
- Docker client: 29.6.2
- Docker server: 29.2.1
- Docker VM: Ubuntu 24.04.4 LTS, aarch64
- Storage driver: overlayfs
- Buildx: v0.35.0 using the `colima` Docker driver

## Procedure

All runs used the cache-baseline Dockerfile and:

```bash
/usr/bin/time -p docker build --progress=plain -t <checkpoint> .
```

1. Build the unchanged source after a successful Compose build.
2. Change only `app/main.py` mtime with `touch`, then build again.
3. Add one temporary source-code comment without changing project dependencies, then build again.
4. Remove the temporary comment so the repository returns to the reviewed baseline source.

The timings are one local observation, not a cross-machine benchmark. Cache hit/miss state in the
plain BuildKit output is the primary result.

## Results

| Run | COPY | dependency install RUN | wall time |
|---|---|---|---:|
| unchanged warm build | `CACHED` | `CACHED` | 2.11 s |
| mtime-only change | `CACHED` | `CACHED` | 1.22 s |
| application source bytes changed | executed | executed (8.8 s) | 11.32 s |

The source-only change forced dependency installation because the baseline Dockerfile performs
`COPY . .` before `RUN python -m pip install --no-cache-dir .`. A future checkpoint will change that
structure; this checkpoint intentionally preserves it.
