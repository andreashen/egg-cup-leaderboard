import json
from pathlib import Path

from eggcup_leaderboard.providers.premier_league.normalizer import (
    build_metadata,
    normalize_standings,
)


def test_normalize_standings_maps_rows() -> None:
    fixture_path = Path("tests/fixtures/premier_league/standings_response.json")
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    rows = normalize_standings(payload)

    assert rows[0].team_name == "Arsenal"
    assert rows[0].team_id == "ars"
    assert rows[0].points == 85
    assert rows[0].rank == 1
    assert rows[0].goal_difference == 44


def test_build_metadata_prefers_latest_round() -> None:
    metadata = build_metadata(
        season="2025-26",
        fetched_at="2026-05-29T12:00:00Z",
        latest_round="Matchweek 38",
    )

    assert metadata.latest_round == "Matchweek 38"
    assert metadata.source == "premierleague.com"
    assert metadata.match_progress == "Matchweek 38"
