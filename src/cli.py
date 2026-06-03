"""CLI 命令入口"""

import hashlib
import json
import logging
import sys
from pathlib import Path

import click
import yaml

from src.providers.premierleague import PremierLeagueProvider
from src.scoring.engine import ScoringEngine
from src.site.generator import SiteGenerator
from src.utils.loaders import load_season_config, load_guesses
from src.utils.team_mapper import TeamMapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

WORKSPACE = Path(__file__).parent.parent


@click.group()
def main() -> None:
    """茶叶蛋杯英超竞猜榜单管理工具"""


@main.command()
@click.option("--season", default="2025-26", help="赛季标识（如 2025-26）")
@click.option("--guesses", default="data/guess_example.csv", help="玩家竞猜 CSV 路径")
@click.option("--artifacts-dir", default="artifacts", help="中间产物保存目录")
@click.option("--site-dir", default="site", help="静态站点输出目录")
@click.option("--config-dir", default="config", help="配置文件目录")
@click.option("--skip-if-unchanged", is_flag=True, help="若数据无变化则跳过生成")
@click.option("--dry-run", is_flag=True, help="仅计算不生成页面")
def update(
    season: str,
    guesses: str,
    artifacts_dir: str,
    site_dir: str,
    config_dir: str,
    skip_if_unchanged: bool,
    dry_run: bool,
) -> None:
    """执行一次完整的抓取→计分→生成流程"""
    base = WORKSPACE
    season_yml = base / "data" / "seasons" / f"{season}.yml"
    baselines_csv = base / "data" / "baselines" / f"{season.split('-')[0]}-{int(season.split('-')[1])-1}_table.csv"

    # 兼容 2025-26 -> 2024-25 的命名
    # 直接从赛季配置里读 baseline_season
    import yaml as _yaml
    with open(season_yml, encoding="utf-8") as f:
        raw_season = _yaml.safe_load(f)
    baseline_season = raw_season["baseline_season"]
    baselines_csv = base / "data" / "baselines" / f"{baseline_season}_table.csv"

    aliases_csv = base / "data" / "team_aliases.csv"
    guesses_csv = base / guesses
    artifacts_path = base / artifacts_dir
    site_path = base / site_dir
    provider_cfg_path = base / config_dir / "provider.yml"
    site_cfg_path = base / config_dir / "site.yml"

    with open(provider_cfg_path, encoding="utf-8") as f:
        provider_cfg = yaml.safe_load(f)
    with open(site_cfg_path, encoding="utf-8") as f:
        site_cfg = yaml.safe_load(f)

    mapper = TeamMapper(aliases_csv)
    season_config = load_season_config(season_yml, baselines_csv)

    logger.info("加载玩家竞猜: %s", guesses_csv)
    player_guesses = load_guesses(guesses_csv, mapper)
    logger.info("共 %d 名玩家", len(player_guesses))

    # 抓取官方数据
    logger.info("开始抓取官方积分榜...")
    provider = PremierLeagueProvider(
        mapper=mapper,
        season_id=provider_cfg.get("current_season_id"),
        timeout=provider_cfg.get("timeout_seconds", 30),
        max_retries=provider_cfg.get("max_retries", 3),
        retry_delay=provider_cfg.get("retry_delay_seconds", 5),
    )

    try:
        snapshot = provider.fetch_snapshot(artifacts_dir=artifacts_path)
    except Exception as exc:
        logger.error("抓取失败: %s", exc)
        sys.exit(1)

    # 检查是否有变化
    if skip_if_unchanged:
        prev_hash_file = artifacts_path / "standings_hash.txt"
        current_hash = _hash_snapshot(artifacts_path / "standings_raw.json")
        if prev_hash_file.exists() and prev_hash_file.read_text().strip() == current_hash:
            logger.info("数据无变化，跳过本次发布。")
            return
        prev_hash_file.write_text(current_hash)

    # 计分
    logger.info("开始计分...")
    engine = ScoringEngine(season=season_config, snapshot=snapshot)
    results = engine.score_all(player_guesses)

    # 保存计分结果
    _save_scoring_results(results, artifacts_path / "scoring_results.json")

    for r in results:
        logger.info("  第%d名 %s: %.1f 分", r.rank, r.nickname, r.total_score)

    if dry_run:
        logger.info("dry-run 模式，跳过页面生成。")
        return

    # 生成静态页面
    logger.info("生成静态站点: %s", site_path)
    gen = SiteGenerator(site_dir=site_path, config=site_cfg)
    gen.generate(results=results, snapshot=snapshot)
    logger.info("完成！")


@main.command()
@click.option("--season", default="2025-26", help="赛季标识")
@click.option("--guesses", default="data/guess_example.csv", help="玩家竞猜 CSV 路径")
@click.option("--artifacts-dir", default="artifacts", help="中间产物目录（已有快照）")
def score(season: str, guesses: str, artifacts_dir: str) -> None:
    """仅执行计分（使用已有快照，不重新抓取）"""
    base = WORKSPACE
    season_yml = base / "data" / "seasons" / f"{season}.yml"

    import yaml as _yaml
    with open(season_yml, encoding="utf-8") as f:
        raw_season = _yaml.safe_load(f)
    baseline_season = raw_season["baseline_season"]
    baselines_csv = base / "data" / "baselines" / f"{baseline_season}_table.csv"

    aliases_csv = base / "data" / "team_aliases.csv"
    guesses_csv = base / guesses
    artifacts_path = base / artifacts_dir

    mapper = TeamMapper(aliases_csv)
    season_config = load_season_config(season_yml, baselines_csv)
    player_guesses = load_guesses(guesses_csv, mapper)

    # 从已有规范化快照加载
    normalized = artifacts_path / "standings_normalized.json"
    if not normalized.exists():
        logger.error("未找到快照文件: %s，请先运行 update 命令", normalized)
        sys.exit(1)

    from src.models.snapshot import StandingsSnapshot, TeamStanding, MatchdayInfo
    from datetime import datetime, timezone

    with open(normalized, encoding="utf-8") as f:
        raw = json.load(f)

    standings: dict[int, TeamStanding] = {}
    standings_by_name: dict[str, TeamStanding] = {}
    for row in raw["standings"]:
        ts = TeamStanding(
            rank=row["rank"],
            standard_name=row["team"],
            played=row["played"],
            won=row["won"],
            drawn=row["drawn"],
            lost=row["lost"],
            goals_for=row["gf"],
            goals_against=row["ga"],
            goal_difference=row["gd"],
            points=row["points"],
        )
        standings[ts.rank] = ts
        standings_by_name[ts.standard_name] = ts

    md = raw.get("matchday")
    matchday = (
        MatchdayInfo(
            latest_completed_matchday=md["latest_completed"],
            total_matchdays=md["total"],
            description=md["description"],
        )
        if md
        else None
    )

    snapshot = StandingsSnapshot(
        fetched_at=datetime.fromisoformat(raw["fetched_at"]),
        source=raw["source"],
        matchday=matchday,
        standings=standings,
        standings_by_name=standings_by_name,
    )

    engine = ScoringEngine(season=season_config, snapshot=snapshot)
    results = engine.score_all(player_guesses)
    _save_scoring_results(results, artifacts_path / "scoring_results.json")
    for r in results:
        click.echo(f"  第{r.rank}名 {r.nickname}: {r.total_score:.1f} 分")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _save_scoring_results(results: list, path: Path) -> None:
    import dataclasses

    def _to_dict(obj):
        if dataclasses.is_dataclass(obj):
            return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
        if isinstance(obj, list):
            return [_to_dict(i) for i in obj]
        return obj

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([_to_dict(r) for r in results], f, ensure_ascii=False, indent=2)
    logger.info("计分结果已保存: %s", path)


def _hash_snapshot(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h


if __name__ == "__main__":
    main()
