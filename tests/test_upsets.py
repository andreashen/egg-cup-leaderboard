from eggcup_leaderboard.scoring.upsets import (
    is_invalid_dark_donkey_pick,
    score_dark_donkey_pick,
    score_dark_horse_pick,
)


def test_score_dark_horse_pick_rewards_team_points_when_rank_improves_by_three() -> None:
    score = score_dark_horse_pick(
        baseline_rank=15,
        current_rank=5,
        current_points=70,
        fallback_points=60,
    )

    assert score == 70


def test_score_dark_horse_pick_penalizes_fallback_rank_points_when_failed() -> None:
    score = score_dark_horse_pick(
        baseline_rank=15,
        current_rank=13,
        current_points=40,
        fallback_points=45,
    )

    assert score == -45


def test_score_dark_donkey_pick_rewards_baseline_points_when_rank_drops_by_three() -> None:
    score = score_dark_donkey_pick(
        baseline_points=66,
        baseline_rank=6,
        current_rank=10,
        current_points=50,
    )

    assert score == 66


def test_invalid_dark_donkey_pick_blocks_promoted_teams() -> None:
    assert is_invalid_dark_donkey_pick(is_promoted=True) is True
