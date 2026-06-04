from eggcup_leaderboard.scoring.common import TOP_FOUR_MAX_POINTS


def score_top_four_pick(
    target_rank: int, predicted_team_points: int, actual_rank_points: int
) -> float:
    base = TOP_FOUR_MAX_POINTS[target_rank]
    return base * (1 - abs(predicted_team_points - actual_rank_points) / 20)
