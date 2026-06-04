from eggcup_leaderboard.scoring.models import PlayerPrediction
from pathlib import Path

from eggcup_leaderboard.inputs.aliases import load_alias_map
from eggcup_leaderboard.inputs.predictions import load_predictions


def test_player_prediction_keeps_multiple_upset_picks() -> None:
    prediction = PlayerPrediction(
        uid="1",
        nickname="中华小当家",
        top_four=["ars", "mci", "liv", "mun"],
        dark_horses=["mun", "tot"],
        dark_donkeys=["bre", "bou"],
    )

    assert prediction.dark_horses == ["mun", "tot"]
    assert prediction.dark_donkeys == ["bre", "bou"]


def test_load_predictions_splits_upset_lists() -> None:
    predictions = load_predictions(
        csv_path=Path("tests/fixtures/scoring/predictions.csv"),
        alias_map=load_alias_map(Path("tests/fixtures/scoring/team_aliases.csv")),
    )

    assert predictions[0].top_four == ["ars", "mci", "liv", "mun"]
    assert predictions[0].dark_horses == ["mun", "tot"]
    assert predictions[0].dark_donkeys == ["bre", "bou"]


def test_load_predictions_skips_non_player_rows_and_trims_nickname() -> None:
    predictions = load_predictions(
        csv_path=Path("tests/fixtures/scoring/predictions.csv"),
        alias_map=load_alias_map(Path("tests/fixtures/scoring/team_aliases.csv")),
    )

    assert len(predictions) == 1
    assert predictions[0].uid == "1"
    assert predictions[0].nickname == "中华小当家"
