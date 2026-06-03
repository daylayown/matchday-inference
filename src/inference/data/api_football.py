"""API-Football v3 client. Direct channel (api-sports.io).

Minimal — just enough to power the Phase 0 data spike. Disk-caches every
response under output/cache/api-football/ so re-runs don't burn rate limit.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

BASE_URL = "https://v3.football.api-sports.io"
DEFAULT_CACHE_DIR = Path("output/cache/api-football")


class APIFootballClient:
    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        timeout: float = 30.0,
    ):
        key = api_key or os.environ.get("API_FOOTBALL_KEY")
        if not key:
            raise RuntimeError("API_FOOTBALL_KEY not set in env")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            base_url=BASE_URL,
            headers={"x-apisports-key": key},
            timeout=timeout,
        )

    def _cache_path(self, endpoint: str, params: dict) -> Path:
        key = endpoint.strip("/").replace("/", "_")
        if params:
            param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
            key = f"{key}__{param_str}"
        return self.cache_dir / f"{key}.json"

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
        use_cache: bool = True,
    ) -> dict:
        params = params or {}
        cache_file = self._cache_path(endpoint, params)
        if use_cache and cache_file.exists():
            return json.loads(cache_file.read_text())
        response = self.client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        cache_file.write_text(json.dumps(data, indent=2))
        return data

    def fixtures(self, **params) -> dict:
        return self.get("/fixtures", params)

    def fixture_lineups(self, fixture_id: int) -> dict:
        return self.get("/fixtures/lineups", {"fixture": fixture_id})

    def fixture_events(self, fixture_id: int) -> dict:
        return self.get("/fixtures/events", {"fixture": fixture_id})

    def fixture_team_statistics(self, fixture_id: int) -> dict:
        return self.get("/fixtures/statistics", {"fixture": fixture_id})

    def fixture_player_statistics(self, fixture_id: int) -> dict:
        return self.get("/fixtures/players", {"fixture": fixture_id})

    def standings(self, league: int, season: int) -> dict:
        return self.get("/standings", {"league": league, "season": season})

    def top_scorers(self, league: int, season: int) -> dict:
        return self.get("/players/topscorers", {"league": league, "season": season})

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
