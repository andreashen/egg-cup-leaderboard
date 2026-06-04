import csv
import re
from pathlib import Path
from typing import Iterable, List

from eggcup_leaderboard.inputs.aliases import normalize_alias
from eggcup_leaderboard.scoring.models import PlayerPrediction

_TOP_FOUR_COLUMNS = ("英超第1", "英超第2", "英超第3", "英超第4")
_MULTI_PICK_SPLITTER = re.compile(r"[、,，]+")


def _split_multi_pick(value: str) -> List[str]:
    return [item.strip() for item in _MULTI_PICK_SPLITTER.split(value) if item.strip()]


def _resolve_team_ids(values: Iterable[str], alias_map: dict[str, str]) -> List[str]:
    return [alias_map[normalize_alias(value)] for value in values]


def load_predictions(csv_path: Path, alias_map: dict[str, str]) -> List[PlayerPrediction]:
    predictions: List[PlayerPrediction] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["玩家类型"].strip() != "玩家":
                continue

            top_four = _resolve_team_ids((row[column] for column in _TOP_FOUR_COLUMNS), alias_map)
            dark_horses = _resolve_team_ids(_split_multi_pick(row["黑马"]), alias_map)
            dark_donkeys = _resolve_team_ids(_split_multi_pick(row["黑驴"]), alias_map)

            predictions.append(
                PlayerPrediction(
                    uid=row["UID"].strip(),
                    nickname=row["玩家昵称"].strip(),
                    top_four=top_four,
                    dark_horses=dark_horses,
                    dark_donkeys=dark_donkeys,
                )
            )

    return predictions
