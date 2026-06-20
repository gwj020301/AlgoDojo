# Multi-stage image for the AlgoDojo backend.
# Build context is the REPO ROOT (the backend depends on the local ./judge
# package via a path dependency, so both directories must be in context).
#
#   docker build -f deploy/Dockerfile --target api    -t algodojo-api .
#   docker build -f deploy/Dockerfile --target worker -t algodojo-worker .

# ---------- base: install deps (backend + judge path dep) ----------
FROM python:3.12-slim AS base

RUN pip install --no-cache-dir uv

WORKDIR /app
# The judge package is a path dependency of the backend (../judge).
COPY judge/ /app/judge/
COPY backend/ /app/backend/

WORKDIR /app/backend
# Install runtime deps only (no dev group). Resolves ../judge editable.
RUN uv sync --no-dev

ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# ---------- api: FastAPI server ----------
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------- worker: judge consumer (needs the docker CLI) ----------
FROM base AS worker
# Just the docker CLI binary — the worker launches sandbox containers via the
# host's Docker daemon (socket mounted at runtime). No daemon installed here.
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker
CMD ["python", "-m", "app.submissions.worker"]
