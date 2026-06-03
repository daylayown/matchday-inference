"""Data spike: pull WC 2022 final (Argentina vs France) through API-Football.

Per api-research.md, this answers one binary question:
    Can API-Football alone provide enough structured truth for a daily casual fanzine?

Output: a coverage report — which fields populate, which are null, which are
absent — for every endpoint we plan to lean on in production.
"""

from __future__ import annotations

import click
from dotenv import load_dotenv

from inference.data.api_football import APIFootballClient

load_dotenv()

WC_LEAGUE_ID = 1
WC_2022_SEASON = 2022
FINAL_DATE = "2022-12-18"


def field_report(data, max_depth: int = 3, max_lines: int = 40) -> list[str]:
    """Walk a JSON structure and print one line per leaf with OK/NULL/EMPTY."""
    lines: list[str] = []

    def walk(node, path: str, depth: int):
        if depth > max_depth or len(lines) >= max_lines:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{path}.{k}" if path else k
                if v is None:
                    lines.append(f"  NULL  {p}")
                elif isinstance(v, dict):
                    if not v:
                        lines.append(f"  EMPTY {p}")
                    else:
                        walk(v, p, depth + 1)
                elif isinstance(v, list):
                    if not v:
                        lines.append(f"  EMPTY {p} (list)")
                    else:
                        lines.append(f"  LIST  {p} ({len(v)} items)")
                        walk(v[0], f"{p}[0]", depth + 1)
                else:
                    lines.append(f"  OK    {p} = {repr(v)[:70]}")
        elif isinstance(node, list):
            if node:
                walk(node[0], f"{path}[0]", depth + 1)

    walk(data, "", 0)
    return lines


def section(title: str):
    click.echo("")
    click.echo(f"=== {title} ===")


@click.command()
@click.option(
    "--no-cache",
    is_flag=True,
    help="Bypass disk cache (force fresh API calls — uses rate limit)",
)
def main(no_cache: bool):
    use_cache = not no_cache
    client = APIFootballClient()

    # 1. Find the final via date filter.
    section(f"/fixtures  (league={WC_LEAGUE_ID} season={WC_2022_SEASON} date={FINAL_DATE})")
    fixtures = client.get(
        "/fixtures",
        {"league": WC_LEAGUE_ID, "season": WC_2022_SEASON, "date": FINAL_DATE},
        use_cache=use_cache,
    )
    if fixtures.get("errors"):
        click.echo(f"  API errors: {fixtures['errors']}")
    response = fixtures.get("response", [])
    click.echo(f"  found {len(response)} fixture(s)")
    if not response:
        click.echo("  cannot continue — no fixture")
        return
    final = response[0]
    fixture_id = final["fixture"]["id"]
    home = final["teams"]["home"]["name"]
    away = final["teams"]["away"]["name"]
    score_h = final["goals"]["home"]
    score_a = final["goals"]["away"]
    click.echo(f"  fixture id: {fixture_id}")
    click.echo(f"  {home} {score_h} — {score_a} {away}")
    for line in field_report(final, max_lines=30):
        click.echo(line)

    # 2. Lineups
    section(f"/fixtures/lineups  (fixture={fixture_id})")
    lineups = client.get(
        "/fixtures/lineups", {"fixture": fixture_id}, use_cache=use_cache
    )
    response = lineups.get("response", [])
    click.echo(f"  {len(response)} team blocks")
    for line in field_report(response, max_lines=25):
        click.echo(line)

    # 3. Events (goals, cards, subs, VAR)
    section(f"/fixtures/events  (fixture={fixture_id})")
    events = client.get(
        "/fixtures/events", {"fixture": fixture_id}, use_cache=use_cache
    )
    response = events.get("response", [])
    click.echo(f"  {len(response)} events")
    event_types: dict[str, int] = {}
    for e in response:
        et = e.get("type", "?")
        event_types[et] = event_types.get(et, 0) + 1
    click.echo(f"  type counts: {event_types}")
    if response:
        for line in field_report(response[0], max_lines=15):
            click.echo(line)

    # 4. Team-level statistics
    section(f"/fixtures/statistics  (fixture={fixture_id})")
    stats = client.get(
        "/fixtures/statistics", {"fixture": fixture_id}, use_cache=use_cache
    )
    response = stats.get("response", [])
    for team_block in response:
        team = team_block.get("team", {}).get("name", "?")
        click.echo(f"  team: {team}")
        for s in team_block.get("statistics", []):
            click.echo(f"    {s.get('type', '?'):<28} {s.get('value')}")

    # 5. Per-player statistics
    section(f"/fixtures/players  (fixture={fixture_id})")
    players = client.get(
        "/fixtures/players", {"fixture": fixture_id}, use_cache=use_cache
    )
    response = players.get("response", [])
    click.echo(f"  {len(response)} team blocks")
    if response:
        first_team = response[0]
        team = first_team.get("team", {}).get("name", "?")
        player_list = first_team.get("players", [])
        click.echo(f"  team: {team} — {len(player_list)} players")
        if player_list:
            first_player = player_list[0]
            click.echo(f"  sample player: {first_player.get('player', {}).get('name')}")
            for line in field_report(first_player, max_lines=30):
                click.echo(line)

    # 6. Standings — group context
    section(f"/standings  (league={WC_LEAGUE_ID} season={WC_2022_SEASON})")
    standings = client.get(
        "/standings",
        {"league": WC_LEAGUE_ID, "season": WC_2022_SEASON},
        use_cache=use_cache,
    )
    response = standings.get("response", [])
    click.echo(f"  {len(response)} league block(s)")
    if response:
        groups = response[0].get("league", {}).get("standings", [])
        click.echo(f"  {len(groups)} groups/stages reported")
        if groups and groups[0]:
            sample_row = groups[0][0]
            click.echo(f"  sample row from first group:")
            for line in field_report(sample_row, max_lines=20):
                click.echo(line)

    # 7. Top scorers
    section(f"/players/topscorers  (league={WC_LEAGUE_ID} season={WC_2022_SEASON})")
    scorers = client.get(
        "/players/topscorers",
        {"league": WC_LEAGUE_ID, "season": WC_2022_SEASON},
        use_cache=use_cache,
    )
    response = scorers.get("response", [])
    click.echo(f"  {len(response)} top scorers returned")
    if response:
        for line in field_report(response[0], max_lines=25):
            click.echo(line)

    client.close()

    section("DONE")
    click.echo("  raw responses cached at output/cache/api-football/")
    click.echo("  re-run without flags to use the cache; --no-cache to refresh")


if __name__ == "__main__":
    main()
