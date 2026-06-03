"""HTTP signup endpoint for THE INFERENCE.

FastAPI app. The landing-page signup form POSTs here; the form data becomes a
ReaderProfile + email and lands in SQLite.

Run locally:
    pip install -e '.[web]'
    uvicorn inference.subscribers.api:app --reload --port 8000

The shape of the form payload matches the ReaderProfile fields plus `email`.
The `slug` is server-generated unless provided.

This is intentionally tiny — no auth, no rate limiting, no double-opt-in
email yet. Stand it up behind any reverse proxy + add the rest when needed.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from ..data.models import Length, Lens, ReaderProfile
from .store import SubscriberStore

app = FastAPI(title="THE INFERENCE — signup")

# CORS: lock to the landing-page origin in prod via INFERENCE_ALLOWED_ORIGINS
# (comma-separated). Defaults to "*" for local dev / pre-domain testing.
_origins = os.environ.get("INFERENCE_ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _origins == "*" else [o.strip() for o in _origins.split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Shared secret guarding the /export endpoint that the daily orchestrator
# (GitHub Actions) calls to pull the live subscriber list. Set in Fly secrets
# and the matching GH Actions secret. If unset, /export is disabled (503).
_EXPORT_TOKEN = os.environ.get("INFERENCE_EXPORT_TOKEN")


class SignupRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    teams: list[str] = Field(min_length=1, max_length=4)
    players: list[str] = Field(default_factory=list, max_length=8)
    lens: Lens
    length: Length = "Standard"
    wildcard: str | None = Field(default=None, max_length=400)
    location: str | None = Field(default=None, max_length=120)
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9-]+$")


class SignupResponse(BaseModel):
    status: Literal["created", "exists"]
    slug: str


def get_store() -> SubscriberStore:
    """Module-level store; FastAPI dependency injection point if you want to swap."""
    return SubscriberStore()


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok"}


@app.post("/signup", response_model=SignupResponse)
def signup(req: SignupRequest) -> SignupResponse:
    store = get_store()
    slug = req.slug or SubscriberStore.generate_slug(req.display_name)
    profile = ReaderProfile(
        slug=slug,
        display_name=req.display_name,
        teams=req.teams,
        players=req.players,
        lens=req.lens,
        length=req.length,
        wildcard=req.wildcard,
        location=req.location,
    )
    try:
        store.create(email=req.email, profile=profile)
        return SignupResponse(status="created", slug=slug)
    except sqlite3.IntegrityError as exc:
        if "subscribers.email" in str(exc):
            raise HTTPException(status_code=409, detail="email_exists")
        if "subscribers.slug" in str(exc):
            raise HTTPException(status_code=409, detail="slug_exists")
        raise


@app.get("/export")
def export(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Return the active subscriber list for the daily orchestrator.

    Auth: `Authorization: Bearer <INFERENCE_EXPORT_TOKEN>`. The GitHub Actions
    cron calls this at the start of each run, writes the result to readers.json,
    then generates issues. Keeps the subscriber DB as a single source of truth
    on the Fly volume — GH Actions never needs direct file access.

    The shape matches `data/readers.json`: {"readers": [ReaderProfile, ...]},
    with each entry carrying an extra `email` so the orchestrator can send
    without direct DB access. `ReaderProfile` ignores the extra key on load.
    """
    if not _EXPORT_TOKEN:
        raise HTTPException(status_code=503, detail="export_disabled")
    expected = f"Bearer {_EXPORT_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")
    store = get_store()
    readers = []
    for p in store.list_active():
        entry = p.model_dump()
        entry["email"] = store.get_email(p.slug)
        readers.append(entry)
    return {"readers": readers}


@app.post("/unsubscribe")
def unsubscribe(slug: str) -> dict[str, str]:
    store = get_store()
    if store.get(slug) is None:
        raise HTTPException(status_code=404, detail="unknown_slug")
    store.unsubscribe(slug)
    return {"status": "unsubscribed", "slug": slug}
