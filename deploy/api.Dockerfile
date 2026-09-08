# =============================================================================
# deploy/api.Dockerfile — drydocs-api (ADR 0005), the thin read API
# =============================================================================
# Build context is the REPO ROOT (compose.yaml sets it), because the API imports
# drydocs_core and reads config/ — the component is not self-contained by
# design, and a context rooted at drydocs_api/ could not see either.
#
# Python 3.11 because pyproject declares `python = "^3.11"`: the floor is what a
# container should pin, so an image that builds here builds on every interpreter
# the project claims to support.
FROM python:3.11-slim

# poetry EXACT, for the reason ruff is pinned exact in pyproject: a resolver that
# picks the day's version is a build that differs between two machines for no
# reason anyone recorded. 2.4.1 is what the producer runs.
ENV POETRY_VERSION=2.4.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Dependencies BEFORE the source, so an ordinary code edit re-runs neither the
# resolve nor the install — the layer cache is the difference between a 4-second
# rebuild and a 4-minute one, and this is the only ordering that gets it.
COPY pyproject.toml poetry.lock ./
# `--only main,api` and not `--with api`: the api group is optional (ADR 0005 keeps
# the default install framework-free) and `--with` would ALSO drag in the dev group
# — pytest, mypy, testcontainers — none of which a server runs.
RUN poetry install --only main,api --no-root

COPY . .

# NOT installed as a package: the server is started as a module path against the
# repo root, exactly as the runbook's Startup step 2 does on the host, so the
# stack exercises the same import surface a developer does.
ENV PYTHONPATH=/app

# 0.0.0.0, not the runbook's implicit localhost. A server bound to 127.0.0.1 in a
# container is reachable only from inside that container, which presents to the
# proxy as a connection refused and reads as "the API is down" — a whole
# debugging session for one missing flag.
EXPOSE 8001
CMD ["uvicorn", "drydocs_api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8001"]
