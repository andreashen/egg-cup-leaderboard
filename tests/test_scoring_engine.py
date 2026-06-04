from eggcup_leaderboard.scoring.engine import rank_players
from eggcup_leaderboard.scoring.models import PlayerPrediction


def test_rank_players_matches_rule_example_total_score() -> None:
    standings = [
        {"team_id": "che", "rank": 1, "points": 90},
        {"team_id": "ars", "rank": 2, "points": 88},
        {"team_id": "liv", "rank": 3, "points": 88},
        {"team_id": "wol", "rank": 4, "points": 75},
        {"team_id": "mun", "rank": 5, "points": 70},
        {"team_id": "mci", "rank": 6, "points": 60},
        {"team_id": "bou", "rank": 13, "points": 30},
    ]
    baseline = {
        "che": {"rank": 4, "points": 69, "is_promoted": False},
        "liv": {"rank": 1, "points": 84, "is_promoted": False},
        "mun": {"rank": 15, "points": 42, "is_promoted": False},
        "ars": {"rank": 2, "points": 74, "is_promoted": False},
        "bou": {"rank": 9, "points": 56, "is_promoted": False},
        "mci": {"rank": 3, "points": 71, "is_promoted": False},
        "wol": {"rank": 16, "points": 42, "is_promoted": False},
    }
    prediction = PlayerPrediction(
        uid="1",
        nickname="小明",
        top_four=["che", "liv", "mun", "ars"],
        dark_horses=["mun", "bou"],
        dark_donkeys=["che", "mci"],
    )

    results = rank_players([prediction], standings=standings, baseline=baseline)

    assert round(results[0].total_score, 2) == 636.0
    assert results[0].rank == 1
