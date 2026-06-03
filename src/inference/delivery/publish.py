"""Publish rendered issues to Cloudflare R2 for the 'view in browser' flow.

Email clients strip the grunge aesthetic (custom properties, web fonts, the
photocopy grain), so the full issue lives on the web instead: each rendered
issue is uploaded to an R2 bucket under an unguessable token key, and the email
teaser links to its public r2.dev URL. The issue HTML is self-contained, so a
single object renders the complete zine.

Uploads shell out to `wrangler r2 object put --remote`, reusing the same
CLOUDFLARE_API_TOKEN the Pages deploy uses (in CI that token needs R2 write).
"""

from __future__ import annotations

import os
import secrets
import subprocess
import tempfile
from pathlib import Path

# Defaults can be overridden by env so CI / a custom domain need no code change.
DEFAULT_BUCKET = os.environ.get("R2_ISSUES_BUCKET", "matchday-inference-issues")
DEFAULT_PUBLIC_BASE = os.environ.get(
    "R2_ISSUES_BASE_URL",
    "https://pub-229d92135b3f4b14a1ae05cf0e25f9f0.r2.dev",
)


def new_token(nbytes: int = 12) -> str:
    """An unguessable URL-safe token — the issue's only access control."""
    return secrets.token_urlsafe(nbytes)


def issue_key(token: str) -> str:
    return f"{token}.html"


def public_url(token: str, base_url: str = DEFAULT_PUBLIC_BASE) -> str:
    return f"{base_url.rstrip('/')}/{issue_key(token)}"


def publish_issue(
    html: str | None = None,
    *,
    html_path: Path | str | None = None,
    token: str | None = None,
    bucket: str = DEFAULT_BUCKET,
    base_url: str = DEFAULT_PUBLIC_BASE,
) -> str:
    """Upload one issue's HTML to R2; return its public URL.

    Provide either `html` (a string) or `html_path` (a file). A token is
    generated if not supplied. Raises CalledProcessError if wrangler fails.
    """
    token = token or new_token()
    key = issue_key(token)

    tmp_name: str | None = None
    if html_path is None:
        if html is None:
            raise ValueError("publish_issue needs either html or html_path")
        tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
        tmp.write(html)
        tmp.close()
        src = tmp.name
        tmp_name = tmp.name
    else:
        src = str(html_path)

    try:
        subprocess.run(
            [
                "npx", "wrangler", "r2", "object", "put", f"{bucket}/{key}",
                "--file", src,
                "--content-type", "text/html; charset=utf-8",
                "--remote",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass

    return public_url(token, base_url)
