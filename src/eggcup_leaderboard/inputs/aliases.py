import csv
from pathlib import Path


def normalize_alias(value: str) -> str:
    return value.strip().casefold()


def load_alias_map(csv_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            alias = normalize_alias(row["alias"])
            mapping[alias] = row["team_id"].strip()

    return mapping
