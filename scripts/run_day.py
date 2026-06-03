"""Run the daily orchestrator for one date.

Usage:
    .venv/bin/python scripts/run_day.py 2022-12-18
    .venv/bin/python scripts/run_day.py 2022-12-18 --issue 04

Reads readers from `data/readers.json` (a list of ReaderProfile dicts);
falls back to a built-in Marcus profile if missing. Loads
`data/patches/<date>.json` if present for editorial seeds + overrides.
"""

from __future__ import annotations

import json
from pathlib import Path

import click
from dotenv import load_dotenv

from inference.data.models import ReaderProfile
from inference.delivery.dispatch import send_results
from inference.orchestrate.daily import run_for_date
from inference.subscribers.store import DEFAULT_DB_PATH, SubscriberStore

load_dotenv()

READERS_FILE = Path("data/readers.json")


def _default_readers() -> list[ReaderProfile]:
    return [
        ReaderProfile(
            slug="marcus",
            display_name="Marcus",
            teams=["Argentina", "France", "Morocco"],
            players=["Lionel Messi", "Kylian Mbappé", "Achraf Hakimi"],
            lens="Cultural Critic",
            length="Standard",
            wildcard=(
                "I'm a chef. Food metaphors and kitchen-language when they "
                "actually fit — don't force it."
            ),
            location="Brooklyn, NY",
        ),
    ]


def _load_readers(source: str) -> list[ReaderProfile]:
    """Load readers from one of: 'sqlite' (the subscriber store), 'json'
    (data/readers.json), or 'default' (a built-in Marcus profile).
    """
    if source == "sqlite":
        if not DEFAULT_DB_PATH.exists():
            click.echo(f"  (no {DEFAULT_DB_PATH} — falling back to json)")
            return _load_readers("json")
        store = SubscriberStore()
        readers = store.list_active()
        store.close()
        click.echo(f"  loaded {len(readers)} active subscribers from {DEFAULT_DB_PATH}")
        return readers
    if source == "json":
        if not READERS_FILE.exists():
            click.echo(f"  (no {READERS_FILE} — using built-in Marcus profile)")
            return _default_readers()
        data = json.loads(READERS_FILE.read_text())
        # Accept both a bare list and the {"readers": [...]} envelope returned by
        # the /export endpoint (which daily.yml curls straight into this file).
        if isinstance(data, dict):
            data = data.get("readers", [])
        return [ReaderProfile.model_validate(r) for r in data]
    return _default_readers()


@click.command()
@click.argument("date_iso")
@click.option("--issue", "issue_number", default="01")
@click.option(
    "--reader-slug",
    default=None,
    help="Run only the reader with this slug (otherwise: all loaded readers).",
)
@click.option(
    "--source",
    type=click.Choice(["sqlite", "json", "default"]),
    default="json",
    help="Where to load readers from. sqlite → data/subscribers.sqlite; "
    "json → data/readers.json; default → built-in Marcus.",
)
@click.option(
    "--send",
    is_flag=True,
    default=False,
    help="After rendering, email each issue via Resend. Requires RESEND_API_KEY "
    "and an email on file for each reader's slug in the subscriber store.",
)
def main(date_iso: str, issue_number: str, reader_slug: str | None, source: str, send: bool):
    readers = _load_readers(source)
    if reader_slug:
        readers = [r for r in readers if r.slug == reader_slug]
        if not readers:
            raise click.ClickException(f"no reader with slug={reader_slug!r}")

    click.echo(f"DATE={date_iso} ISSUE=N°{issue_number} READERS={len(readers)}")
    results = run_for_date(date_iso, readers, issue_number=issue_number)

    click.echo("")
    total_cost = 0.0
    for r in results:
        click.echo(f"  {r.summary()}")
        total_cost += r.total_cost_usd
        if r.error:
            click.echo(f"    ! {r.error.splitlines()[0]}")
    click.echo("")
    click.echo(f"DONE  readers={len(results)} total_cost=${total_cost:.4f}")

    if send:
        click.echo("")
        click.echo("SENDING via Resend …")
        outcomes = send_results(
            results, readers, date_iso=date_iso, issue_number=issue_number
        )
        for o in outcomes:
            click.echo(str(o))
        sent = sum(1 for o in outcomes if o.sent)
        click.echo("")
        click.echo(f"SENT  {sent}/{len(outcomes)}")


if __name__ == "__main__":
    main()
