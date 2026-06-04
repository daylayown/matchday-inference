"""SQLite store for subscribers.

One file, stdlib `sqlite3`. Persist enough to run the daily orchestrator
against the real list of readers, plus an email address for delivery and a
verified-at timestamp. Single opt-in: `create()` sets verified_at by default,
so a signup is active immediately. The column still exists (and `verify()`
still works) so a double-opt-in flow can be layered on later.

Schema:
  subscribers(
    slug TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    profile_json TEXT NOT NULL,      -- ReaderProfile as JSON
    created_at TEXT NOT NULL,        -- ISO timestamp
    verified_at TEXT,                -- ISO timestamp; null = unverified
    unsubscribed_at TEXT             -- ISO timestamp; null = active
  )

The `profile_json` holds the full ReaderProfile (teams, lens, length,
wildcard, location, players). Storing the whole thing as JSON keeps schema
churn out of the SQL layer — every new ReaderProfile field is automatically
persisted.
"""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..data.models import ReaderProfile

# Path resolution order: explicit constructor arg → INFERENCE_DB_PATH env var →
# the local default. The env var lets the Fly.io deployment point the store at a
# persistent volume (e.g. /data/subscribers.sqlite) without code changes.
DEFAULT_DB_PATH = Path(os.environ.get("INFERENCE_DB_PATH", "data/subscribers.sqlite"))


SCHEMA = """
CREATE TABLE IF NOT EXISTS subscribers (
    slug TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    verified_at TEXT,
    unsubscribed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_subscribers_active
    ON subscribers (verified_at, unsubscribed_at);
"""


class SubscriberStore:
    """Lightweight wrapper around a SQLite file. Stateless beyond the connection."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    # ─── reads ─────────────────────────────────────────────────────────────

    def list_active(self) -> list[ReaderProfile]:
        """All verified, not-yet-unsubscribed readers as ReaderProfile objects."""
        rows = self._conn.execute(
            "SELECT profile_json FROM subscribers "
            "WHERE verified_at IS NOT NULL AND unsubscribed_at IS NULL"
        ).fetchall()
        return [ReaderProfile.model_validate(json.loads(r["profile_json"])) for r in rows]

    def list_all(self) -> list[dict[str, Any]]:
        """Every subscriber as a metadata dict (slug, email, status, timestamps).

        For admin/CLI use — unlike `list_active`, this includes unverified and
        unsubscribed rows and carries the bookkeeping columns, not the profile.
        `status` is derived: 'unsubscribed' > 'active' (verified) > 'pending'.
        """
        rows = self._conn.execute(
            "SELECT slug, email, display_name, created_at, verified_at, "
            "unsubscribed_at FROM subscribers ORDER BY created_at"
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            if d["unsubscribed_at"]:
                d["status"] = "unsubscribed"
            elif d["verified_at"]:
                d["status"] = "active"
            else:
                d["status"] = "pending"
            out.append(d)
        return out

    def get(self, slug: str) -> ReaderProfile | None:
        row = self._conn.execute(
            "SELECT profile_json FROM subscribers WHERE slug = ?", (slug,)
        ).fetchone()
        if not row:
            return None
        return ReaderProfile.model_validate(json.loads(row["profile_json"]))

    def get_email(self, slug: str) -> str | None:
        row = self._conn.execute(
            "SELECT email FROM subscribers WHERE slug = ?", (slug,)
        ).fetchone()
        return row["email"] if row else None

    # ─── writes ────────────────────────────────────────────────────────────

    def create(
        self, *, email: str, profile: ReaderProfile, verified: bool = True
    ) -> ReaderProfile:
        """Insert a new subscriber. Slug must be unique; email must be unique.

        `verified` defaults to True — this is a single-opt-in publication, so a
        signup is active immediately (it shows up in `list_active`/`/export` and
        will receive issues). Pass `verified=False` to insert a pending row for
        a future double-opt-in flow.

        Raises sqlite3.IntegrityError on conflict.
        """
        now = _now_iso()
        self._conn.execute(
            "INSERT INTO subscribers "
            "(slug, email, display_name, profile_json, created_at, verified_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                profile.slug,
                email.lower().strip(),
                profile.display_name,
                profile.model_dump_json(),
                now,
                now if verified else None,
            ),
        )
        return profile

    def update_profile(self, profile: ReaderProfile) -> None:
        """Replace the profile_json for an existing subscriber (keyed by slug)."""
        self._conn.execute(
            "UPDATE subscribers SET profile_json = ?, display_name = ? WHERE slug = ?",
            (profile.model_dump_json(), profile.display_name, profile.slug),
        )

    def verify(self, slug: str) -> None:
        self._conn.execute(
            "UPDATE subscribers SET verified_at = ? WHERE slug = ?",
            (_now_iso(), slug),
        )

    def unsubscribe(self, slug: str) -> None:
        self._conn.execute(
            "UPDATE subscribers SET unsubscribed_at = ? WHERE slug = ?",
            (_now_iso(), slug),
        )

    # ─── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def generate_slug(display_name: str) -> str:
        """Suggest a slug — kebabified display_name + 4 random chars."""
        base = "".join(c.lower() if c.isalnum() else "-" for c in display_name)
        base = "-".join(p for p in base.split("-") if p) or "reader"
        suffix = secrets.token_hex(2)
        return f"{base}-{suffix}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
