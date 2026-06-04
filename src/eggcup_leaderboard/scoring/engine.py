from typing import Dict, List, Tuple

from eggcup_leaderboard.scoring.models import (
    PlayerPrediction,
    PlayerScoreResult,
    ScoreBreakdown,
)
from eggcup_leaderboard.scoring.top_four import score_top_four_pick
from eggcup_leaderboard.scoring.upsets import (
    is_invalid_dark_donkey_pick,
    is_invalid_dark_horse_pick,
    score_dark_donkey_pick,
    score_dark_horse_pick,
)


def _index_standings(
    rows: List[Dict[str, int]]
) -> Tuple[Dict[str, Dict[str, int]], Dict[int, Dict[str, int]]]:
    by_team = {row["team_id"]: row for row in rows}
    by_rank = {row["rank"]: row for row in rows}
    return by_team, by_rank


def rank_players(
    predictions: List[PlayerPrediction],
    standings: List[Dict[str, int]],
    baseline: Dict[str, Dict[str, object]],
) -> List[PlayerScoreResult]:
    by_team, by_rank = _index_standings(standings)
    results: List[PlayerScoreResult] = []

    for prediction in predictions:
        top_four_scores: List[ScoreBreakdown] = []
        dark_horse_scores: List[ScoreBreakdown] = []
        dark_donkey_scores: List[ScoreBreakdown] = []

        for target_rank, team_id in enumerate(prediction.top_four, start=1):
            predicted_points = by_team[team_id]["points"]
            actual_rank_points = by_rank[target_rank]["points"]
            score = score_top_four_pick(target_rank, predicted_points, actual_rank_points)
            top_four_scores.append(
                ScoreBreakdown(
                    label="top_four",
                    team_id=team_id,
                    score=score,
                    explanation=(
                        "target_rank={0}, predicted_points={1}, actual_rank_points={2}"
                    ).format(target_rank, predicted_points, actual_rank_points),
                )
            )

        for team_id in prediction.dark_horses:
            base = baseline[team_id]
            if is_invalid_dark_horse_pick(base["rank"]):
                score = 0.0
                explanation = "invalid dark horse pick"
            else:
                current_rank = by_team[team_id]["rank"]
                current_points = by_team[team_id]["points"]
                if base["rank"] - current_rank >= 3:
                    score = float(
                        score_dark_horse_pick(
                            baseline_rank=base["rank"],
                            current_rank=current_rank,
                            current_points=current_points,
                            fallback_points=0,
                        )
                    )
                else:
                    fallback_rank = base["rank"] - 3
                    score = float(
                        score_dark_horse_pick(
                            baseline_rank=base["rank"],
                            current_rank=current_rank,
                            current_points=current_points,
                            fallback_points=by_rank[fallback_rank]["points"],
                        )
                    )
                explanation = "baseline_rank={0}, current_rank={1}".format(
                    base["rank"],
                    current_rank,
                )
            dark_horse_scores.append(
                ScoreBreakdown(
                    label="dark_horse",
                    team_id=team_id,
                    score=score,
                    explanation=explanation,
                )
            )

        for team_id in prediction.dark_donkeys:
            base = baseline[team_id]
            if is_invalid_dark_donkey_pick(base["is_promoted"]):
                score = 0.0
                explanation = "invalid dark donkey pick"
            else:
                score = float(
                    score_dark_donkey_pick(
                        baseline_points=base["points"],
                        baseline_rank=base["rank"],
                        current_rank=by_team[team_id]["rank"],
                        current_points=by_team[team_id]["points"],
                    )
                )
                explanation = "baseline_rank={0}, current_rank={1}".format(
                    base["rank"],
                    by_team[team_id]["rank"],
                )
            dark_donkey_scores.append(
                ScoreBreakdown(
                    label="dark_donkey",
                    team_id=team_id,
                    score=score,
                    explanation=explanation,
                )
            )

        total_score = sum(
            item.score
            for item in top_four_scores + dark_horse_scores + dark_donkey_scores
        )
        results.append(
            PlayerScoreResult(
                uid=prediction.uid,
                nickname=prediction.nickname,
                total_score=total_score,
                rank=0,
                top_four_scores=top_four_scores,
                dark_horse_scores=dark_horse_scores,
                dark_donkey_scores=dark_donkey_scores,
            )
        )

    ordered = sorted(results, key=lambda item: item.total_score, reverse=True)
    for index, result in enumerate(ordered, start=1):
        result.rank = index
    return ordered
