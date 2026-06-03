"""Scaffold a daily editorial patch.

Writes a fill-in-the-blanks `data/patches/<date>.json` with every editorial
seed block stubbed. The per-day patch is the only manual content step in the
pipeline; this turns it into overwriting TODO placeholders.

Usage:
    .venv/bin/python scripts/new_patch.py 2026-06-11
    .venv/bin/python scripts/new_patch.py 2026-06-11 --force      # overwrite
    .venv/bin/python scripts/new_patch.py 2026-06-11 --stdout     # print, don't write
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import click

from inference.data.patch_template import skeleton_patch

PATCHES_DIR = Path("data/patches")


@click.command()
@click.argument("date_iso")
@click.option("--force", is_flag=True, help="Overwrite an existing patch file.")
@click.option("--stdout", "to_stdout", is_flag=True, help="Print JSON instead of writing.")
def main(date_iso: str, force: bool, to_stdout: bool):
    try:
        date.fromisoformat(date_iso)
    except ValueError as exc:
        raise click.ClickException(f"bad date {date_iso!r}: {exc} (want YYYY-MM-DD)")

    skeleton = skeleton_patch(date_iso)
    text = json.dumps(skeleton, indent=2, ensure_ascii=False) + "\n"

    if to_stdout:
        click.echo(text, nl=False)
        return

    PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PATCHES_DIR / f"{date_iso}.json"
    if out_path.exists() and not force:
        raise click.ClickException(f"{out_path} exists — pass --force to overwrite")

    out_path.write_text(text)
    click.echo(f"wrote {out_path}")
    click.echo("Fill in the TODO placeholders; delete any seed block you don't want.")


if __name__ == "__main__":
    main()
