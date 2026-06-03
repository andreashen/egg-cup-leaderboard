"""静态配置和数据文件加载器"""

import csv
import logging
from pathlib import Path

import yaml

from src.models.season import SeasonConfig, TeamBaseline
from src.models.guess import PlayerGuess
from src.utils.team_mapper import TeamMapper

logger = logging.getLogger(__name__)

TOP4_FULL_SCORES = {1: 400, 2: 200, 3: 100, 4: 100}


def load_season_config(season_yml: Path, baselines_csv: Path) -> SeasonConfig:
    """加载赛季配置并整合基线数据"""
    with open(season_yml, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    promoted_map: dict[str, int] = {}
    for p in raw.get("promoted_teams", []):
        promoted_map[p["team"]] = p["baseline_epl_rank"]

    config = SeasonConfig(
        season_id=raw["season_id"],
        season_name=raw["season_name"],
        baseline_season=raw["baseline_season"],
        teams=raw.get("teams", []),
        promoted_teams=promoted_map,
    )

    config.baselines = load_baselines(baselines_csv, promoted_map)
    return config


def load_baselines(baselines_csv: Path, promoted_map: dict[str, int]) -> dict[str, TeamBaseline]:
    """加载上赛季基线积分榜"""
    baselines: dict[str, TeamBaseline] = {}
    with open(baselines_csv, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            standard = row["team"].strip()
            rank = int(row["rank"])
            points = int(row["points"])
            is_promoted = standard in promoted_map
            baselines[standard] = TeamBaseline(
                standard_name=standard,
                rank=rank,
                points=points,
                is_promoted=is_promoted,
            )
    return baselines


def load_guesses(guesses_csv: Path, mapper: TeamMapper) -> list[PlayerGuess]:
    """加载并标准化玩家竞猜 CSV"""
    guesses = []
    with open(guesses_csv, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("玩家类型", "").strip() != "玩家":
                continue

            top4 = [
                mapper.resolve_or_raise(row[f"英超第{i}"].strip())
                for i in range(1, 5)
            ]

            dark_horses = _parse_multi(row.get("黑马", ""), mapper)
            dark_donkeys = _parse_multi(row.get("黑驴", ""), mapper)

            guesses.append(
                PlayerGuess(
                    uid=row["UID"].strip(),
                    nickname=row["玩家昵称"].strip(),
                    top4=top4,
                    dark_horses=dark_horses,
                    dark_donkeys=dark_donkeys,
                )
            )
    return guesses


def _parse_multi(cell: str, mapper: TeamMapper) -> list[str]:
    """解析逗号/顿号分隔的多球队字段"""
    if not cell or not cell.strip():
        return []
    parts = cell.replace("、", ",").split(",")
    return [mapper.resolve_or_raise(p.strip()) for p in parts if p.strip()]
