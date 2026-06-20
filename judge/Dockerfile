# AlgoDojo judge sandbox image.
# Contains Python 3 + Node.js + the TypeScript compiler, plus the stdlib-only
# in-container runner. Runs as a non-root user (defense in depth; the execution
# engine additionally passes --user, --cap-drop ALL, --read-only, --network none).
FROM python:3.12-slim

# Node.js + npm (for running TS-compiled JS) and the TypeScript compiler.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && npm install -g typescript@5.7 @types/node@20 \
    && npm cache clean --force \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install the judge package (stdlib only — no pip install needed).
COPY dojo_judge /opt/judge/dojo_judge
ENV PYTHONPATH=/opt/judge \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run as the unprivileged "nobody" user.
USER 65534:65534

# /tmp is mounted as a writable tmpfs at runtime; user code is mounted at /work (ro).
WORKDIR /tmp

ENTRYPOINT ["python3", "-m", "dojo_judge.runner"]
