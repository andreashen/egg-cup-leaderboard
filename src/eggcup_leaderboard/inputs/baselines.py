import csv
from pathlib import Path

from eggcup_leaderboard.scoring.common import BaselineTable


def load_baseline_rows(csv_path: Path) -> BaselineTable:
    rows: BaselineTable = {}

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[row["team_id"].strip()] = {
                "rank": int(row["rank"]),
                "points": int(row["points"]) if row["points"] else None,
                "is_promoted": row["is_promoted"].strip().lower() == "true",
            }

    return rows
