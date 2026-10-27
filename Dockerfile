# MotoQuant API image — two stages.
#
#   1. rust-builder  compiles the optional Rust physics core (rust/motoquant-core)
#                    into a PyO3 abi3 wheel with maturin.
#   2. runtime       the API itself. Installs that wheel when present; the
#                    engine selector (motoquant/engine_select.py) then runs every
#                    simulation on the Rust core and falls back to the Python
#                    reference engine when the wheel is absent or unusable.
#                    /api/health reports which one is live and why.
#
# Both stages use the SAME Debian release (bookworm, glibc 2.36): pip refuses a
# manylinux wheel that needs a newer glibc than the runtime has, so building
# and running on one release guarantees the wheel installs. glibc/musl note:
# never build this on alpine — the bit-parity contract (docs/RUST_CORE.md)
# relies on the native core calling the same glibc libm as CPython.
#
# Build without the Rust core (pure-Python image, e.g. to bisect a problem):
#   docker build --build-arg MOTOQUANT_NATIVE=0 .

# ── Stage 1: Rust core wheel ─────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS rust-builder

ARG MOTOQUANT_NATIVE=1
# Pinned toolchain (the one the parity sweep was run with) + maturin range
# from rust/motoquant-core/pyproject.toml.
ARG RUST_TOOLCHAIN=1.97.0

RUN mkdir -p /wheels
WORKDIR /build
COPY rust/ ./rust/

# gcc/libc6-dev: the linker rustc drives. `--profile minimal`: rustc + cargo
# only. `--locked`: build exactly rust/Cargo.lock (the crates the parity
# sweep validated) — fail instead of silently resolving newer ones.
RUN if [ "$MOTOQUANT_NATIVE" = "1" ]; then \
      set -eux; \
      apt-get update; \
      apt-get install -y --no-install-recommends ca-certificates curl gcc libc6-dev; \
      rm -rf /var/lib/apt/lists/*; \
      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --profile minimal --default-toolchain "$RUST_TOOLCHAIN"; \
      pip install --no-cache-dir "maturin>=1.5,<2"; \
      cd rust; \
      PATH="/root/.cargo/bin:$PATH" maturin build --release --locked \
        -m motoquant-core/Cargo.toml -o /wheels; \
    else \
      echo "MOTOQUANT_NATIVE=$MOTOQUANT_NATIVE: skipping the Rust core (Python engine only)"; \
    fi

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm

ARG MOTOQUANT_NATIVE=1

WORKDIR /app

# Install dependencies from the fully-pinned lockfile so two builds of the
# same git commit install identical dependency sets (requirements-api.txt is
# the human-maintained source; `make lock` regenerates the lock from it).
COPY requirements-api.lock .
RUN pip install --no-cache-dir -r requirements-api.lock

# The Rust core wheel (directory may be empty when MOTOQUANT_NATIVE=0).
COPY --from=rust-builder /wheels/ /tmp/wheels/
RUN set -eu; \
    if ls /tmp/wheels/*.whl >/dev/null 2>&1; then \
      pip install --no-cache-dir --no-deps /tmp/wheels/*.whl; \
    else \
      echo "no motoquant_core wheel: simulations will use the Python engine"; \
    fi; \
    rm -rf /tmp/wheels

# Copy application code (+ the Apache-2.0 LICENSE, which must travel with
# every redistributed copy — the image is one).
COPY LICENSE .
COPY motoquant/ ./motoquant/
COPY motoquant.db .
COPY artifacts/surrogate/surrogate_numpy.npz ./artifacts/surrogate/surrogate_numpy.npz
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Build-time self-check: print the engine the image will serve with, and fail
# the build if the Rust core was requested, built, and then does not load
# (a broken wheel must not ship silently as a slower Python-only image).
RUN python -c "import json, sys; from motoquant import engine_select, native; \
info = engine_select.engine_info(); print('engine:', json.dumps(info)); \
sys.exit(0 if '$MOTOQUANT_NATIVE' != '1' or native.available() else 'motoquant_core wheel did not load')"

# Run as an unprivileged user. /app must stay writable by it: SQLite creates
# journal/WAL sibling files next to /app/motoquant.db, so the DB's DIRECTORY
# (not just the file) needs write permission.
RUN useradd -m app && chown -R app:app /app

# Render (and Railway before it) inject PORT at runtime
ENV PORT=8000
ENV MOTOQUANT_DB=/app/motoquant.db
# Engine selection: auto (Rust core when loadable, else Python). Set
# MOTOQUANT_ENGINE=python in the host's dashboard as a no-rebuild kill switch.
ENV MOTOQUANT_ENGINE=auto

USER app

# Startup
# Entrypoint seeds a persistent-disk DB on first boot, then execs uvicorn.
# No-op when MOTOQUANT_DB is the baked /app path (current free tier).
CMD ["./docker-entrypoint.sh"]
