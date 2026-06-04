from pathlib import Path

from eggcup_leaderboard.inputs.baselines import load_baseline_rows
from eggcup_leaderboard.scoring.top_four import score_top_four_pick


def test_load_baseline_rows_parses_points_and_promoted_flags() -> None:
    rows = load_baseline_rows(Path("tests/fixtures/scoring/baseline_table.csv"))

    assert rows["liv"] == {"rank": 1, "points": 84, "is_promoted": False}
    assert rows["lee"] == {"rank": 18, "points": None, "is_promoted": True}


def test_score_top_four_pick_uses_target_points_gap() -> None:
    score = score_top_four_pick(
        target_rank=4,
        predicted_team_points=70,
        actual_rank_points=60,
    )

    assert score == 50.0


def test_score_top_four_pick_can_be_negative() -> None:
    score = score_top_four_pick(
        target_rank=1,
        predicted_team_points=10,
        actual_rank_points=90,
    )

    assert score == -1200.0
