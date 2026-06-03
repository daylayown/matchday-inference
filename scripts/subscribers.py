"""Admin CLI for the subscriber store.

Read and manage the SQLite subscriber list without opening sqlite by hand.

Usage:
    .venv/bin/python scripts/subscribers.py list
    .venv/bin/python scripts/subscribers.py list --active
    .venv/bin/python scripts/subscribers.py verify <slug>
    .venv/bin/python scripts/subscribers.py unsubscribe <slug>
    .venv/bin/python scripts/subscribers.py export --out data/readers.json

`--db PATH` overrides the database location on any command (default:
$INFERENCE_DB_PATH or data/subscribers.sqlite).
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from inference.subscribers.store import DEFAULT_DB_PATH, SubscriberStore


@click.group()
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path),
    default=DEFAULT_DB_PATH,
    help="Path to the subscriber SQLite file.",
)
@click.pass_context
def cli(ctx: click.Context, db_path: Path):
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db_path


def _store(ctx: click.Context) -> SubscriberStore:
    return SubscriberStore(db_path=ctx.obj["db_path"])


@cli.command(name="list")
@click.option("--active", is_flag=True, help="Show only active (verified, not unsubscribed).")
@click.pass_context
def list_cmd(ctx: click.Context, active: bool):
    """List subscribers with status."""
    store = _store(ctx)
    try:
        rows = store.list_all()
    finally:
        store.close()
    if active:
        rows = [r for r in rows if r["status"] == "active"]
    if not rows:
        click.echo("(no subscribers)")
        return
    width = max(len(r["slug"]) for r in rows)
    for r in rows:
        click.echo(f"  {r['slug']:<{width}}  {r['status']:<12}  {r['email']}")
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = "  ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    click.echo("")
    click.echo(f"total={len(rows)}  {summary}")


@cli.command()
@click.argument("slug")
@click.pass_context
def verify(ctx: click.Context, slug: str):
    """Mark a subscriber verified (double-opt-in confirm)."""
    store = _store(ctx)
    try:
        if store.get(slug) is None:
            raise click.ClickException(f"no subscriber with slug={slug!r}")
        store.verify(slug)
    finally:
        store.close()
    click.echo(f"verified {slug}")


@cli.command()
@click.argument("slug")
@click.pass_context
def unsubscribe(ctx: click.Context, slug: str):
    """Mark a subscriber unsubscribed."""
    store = _store(ctx)
    try:
        if store.get(slug) is None:
            raise click.ClickException(f"no subscriber with slug={slug!r}")
        store.unsubscribe(slug)
    finally:
        store.close()
    click.echo(f"unsubscribed {slug}")


@cli.command()
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
def export(ctx: click.Context, out_path: Path | None):
    """Dump active readers as JSON (the shape run_day.py --source json reads)."""
    store = _store(ctx)
    try:
        readers = [p.model_dump() for p in store.list_active()]
    finally:
        store.close()
    text = json.dumps(readers, indent=2, ensure_ascii=False) + "\n"
    if out_path is None:
        click.echo(text, nl=False)
    else:
        out_path.write_text(text)
        click.echo(f"wrote {len(readers)} active readers → {out_path}")


if __name__ == "__main__":
    cli()
