# Nyhetsradar — Flask dashboard + collection pipeline.
#
# One image, two roles: `web` serves the brief, `pipeline` runs
# collect -> dedup -> score on a timer. Both share the SQLite volume.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Bytecode compilation trades a slower build for faster container start.
# Copy mode because the cache mount is not the same filesystem as /app.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, in their own layer: they change far less often than
# source, so editing a module does not re-resolve the environment.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY nyhetsradar/ ./nyhetsradar/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim-bookworm AS runtime

# curl is here for the compose healthcheck; nothing in the app shells out.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 nyhet

WORKDIR /app

COPY --from=builder --chown=nyhet:nyhet /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_PATH=/data/news.db

# SQLite lives on a volume so it survives redeploys. The pipeline writes here
# and the web process reads, so both containers mount the same one.
RUN mkdir -p /data && chown nyhet:nyhet /data
VOLUME ["/data"]

COPY --chmod=0755 docker/pipeline-loop.sh /usr/local/bin/pipeline-loop

USER nyhet
EXPOSE 8000

# Two workers is plenty: this is an internal dashboard read by a handful of
# people, and SQLite is the bottleneck long before the WSGI layer is.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", \
     "--access-logfile", "-", "nyhetsradar.app:app"]
