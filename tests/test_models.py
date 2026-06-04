from eggcup_leaderboard.models import Metadata, StandingRow


def test_metadata_defaults_to_empty_match_progress() -> None:
    metadata = Metadata(
        season="2025-26",
        source="premierleague.com",
        fetched_at="2026-05-29T12:00:00Z",
        latest_round=None,
    )

    assert metadata.match_progress is None


def test_standing_row_requires_numeric_points() -> None:
    row = StandingRow(
        team_id="arsenal",
        team_name="Arsenal",
        rank=1,
        points=89,
        played=38,
        won=27,
        drawn=8,
        lost=3,
        goal_difference=48,
    )

    assert row.points == 89
