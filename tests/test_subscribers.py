"""Smoke tests for the subscriber SQLite store."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from inference.data.models import ReaderProfile
from inference.subscribers.store import SubscriberStore


@pytest.fixture
def store(tmp_path: Path) -> SubscriberStore:
    return SubscriberStore(db_path=tmp_path / "test.sqlite")


def _profile(slug: str = "ada") -> ReaderProfile:
    return ReaderProfile(
        slug=slug,
        display_name="Ada Lovelace",
        teams=["England", "Italy"],
        lens="Historian",
        length="Standard",
        wildcard="I'm a mathematician.",
        location="London",
    )


def test_create_and_get(store):
    store.create(email="ada@example.com", profile=_profile())
    out = store.get("ada")
    assert out is not None
    assert out.slug == "ada"
    assert out.location == "London"
    assert store.get_email("ada") == "ada@example.com"


def test_create_duplicate_email_fails(store):
    store.create(email="ada@example.com", profile=_profile("ada"))
    with pytest.raises(sqlite3.IntegrityError):
        store.create(email="ada@example.com", profile=_profile("bee"))


def test_list_active_filters(store):
    store.create(email="a@x.com", profile=_profile("ada"))
    store.create(email="b@x.com", profile=_profile("bee"))
    # Both unverified — neither active
    assert store.list_active() == []
    store.verify("ada")
    active = store.list_active()
    assert len(active) == 1
    assert active[0].slug == "ada"
    # Unsubscribe removes from active
    store.unsubscribe("ada")
    assert store.list_active() == []


def test_update_profile_persists(store):
    store.create(email="a@x.com", profile=_profile("ada"))
    new = _profile("ada")
    new.lens = "Pub-Talker"  # type: ignore[assignment]
    store.update_profile(new)
    out = store.get("ada")
    assert out is not None
    assert out.lens == "Pub-Talker"


def test_list_all_reports_status(store):
    store.create(email="a@x.com", profile=_profile("ada"))
    store.create(email="b@x.com", profile=_profile("bee"))
    store.create(email="c@x.com", profile=_profile("cy"))
    store.verify("bee")
    store.verify("cy")
    store.unsubscribe("cy")

    rows = {r["slug"]: r for r in store.list_all()}
    assert rows["ada"]["status"] == "pending"
    assert rows["bee"]["status"] == "active"
    assert rows["cy"]["status"] == "unsubscribed"
    assert rows["ada"]["email"] == "a@x.com"


def test_generate_slug():
    s = SubscriberStore.generate_slug("Marcus Aurelius")
    assert s.startswith("marcus-aurelius-")
    assert len(s) > len("marcus-aurelius-")
    s2 = SubscriberStore.generate_slug("???")
    assert s2.startswith("reader-")
