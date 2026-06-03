# THE INFERENCE — signup endpoint (FastAPI + SQLite) for Fly.io.
# This image runs ONLY the subscriber API. The daily generator runs on
# GitHub Actions, not here.
FROM python:3.13-slim

# Faster, quieter Python in containers.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first for layer caching. The endpoint needs the package + the
# [web] extra (fastapi + uvicorn). Copy only what the install needs.
COPY pyproject.toml ./
COPY CLAUDE.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install '.[web]'

# The SQLite file lives on a mounted Fly volume; see fly.toml + DEPLOYMENT.md.
ENV INFERENCE_DB_PATH=/data/subscribers.sqlite

EXPOSE 8000

# email-validator (pulled by pydantic[email]) is needed for EmailStr; ensure it.
RUN pip install 'pydantic[email]'

CMD ["uvicorn", "inference.subscribers.api:app", "--host", "0.0.0.0", "--port", "8000"]
