# =============================================================================
# deploy/agent.Dockerfile — the ADK agent server behind the console's Ask module
# =============================================================================
# A SEPARATE IMAGE FROM THE API, AND THAT IS THE POINT. agents/ has always had
# its own interpreter and its own requirements.txt — `poetry run` cannot find
# google-adk, and the agents venv leads the poetry env on the neo4j driver major
# (6.x vs 5.x) on purpose (agents/requirements.txt). Two images is that same
# separation, enforced by construction rather than by remembering which shell to
# be in.
#
# 3.12 rather than the API's 3.11: this venv is declared free to lead, and the
# pinned floors in requirements.txt were measured on a newer interpreter.
FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1

WORKDIR /app/agents

# Requirements first — see the api Dockerfile's note on layer ordering. This one
# matters more: litellm and google-adk pull a large tree.
COPY agents/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./

# serve.py, NOT `adk api_server` (R14): the launcher hands ADK its
# NestedAgentLoader, so /list-apps returns the four real apps and not the shared
# `common/` package as a fifth. The health check in compose.yaml asserts exactly
# that, which makes the wrong launcher a failed start rather than a puzzle.
#
# --host 0.0.0.0 overrides serve.py's 127.0.0.1 default, for the same reason the
# API binds wide: the default is right for a laptop and unreachable in a network
# namespace.
EXPOSE 8000
CMD ["python", "serve.py", "--host", "0.0.0.0", "--port", "8000"]
