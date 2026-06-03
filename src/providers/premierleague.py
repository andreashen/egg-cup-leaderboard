"""Premier League 官方数据源适配层

使用 PulseAPI（footballapi.pulselive.com）获取积分榜和赛程数据。
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from src.models.snapshot import StandingsSnapshot, TeamStanding, MatchdayInfo
from src.utils.team_mapper import TeamMapper

logger = logging.getLogger(__name__)

STANDINGS_URL = (
    "https://footballapi.pulselive.com/football/standings"
    "?compSeasons={season_id}&altIds=true&detail=2&COMP=1&live=true"
)
SEASONS_URL = (
    "https://footballapi.pulselive.com/football/competitions/1/compseasons"
    "?page=0&pageSize=5&detail=2"
)

DEFAULT_HEADERS = {
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


class PremierLeagueProvider:
    def __init__(
        self,
        mapper: TeamMapper,
        season_id: int | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 5,
    ) -> None:
        self.mapper = mapper
        self.season_id = season_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_snapshot(self, artifacts_dir: Path | None = None) -> StandingsSnapshot:
        """抓取当前赛季积分榜，保存原始快照，返回规范化结果"""
        if self.season_id is None:
            self.season_id = self._discover_season_id()

        url = STANDINGS_URL.format(season_id=self.season_id)
        raw = self._get_json(url)

        if artifacts_dir:
            self._save_raw(raw, artifacts_dir / "standings_raw.json")

        snapshot = self._parse_standings(raw)

        if artifacts_dir:
            self._save_normalized(snapshot, artifacts_dir / "standings_normalized.json")

        return snapshot

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _discover_season_id(self) -> int:
        """自动获取最新赛季 ID"""
        data = self._get_json(SEASONS_URL)
        seasons = data.get("content", [])
        if not seasons:
            raise RuntimeError("无法获取赛季列表")
        latest = seasons[0]
        season_id = latest["id"]
        logger.info("发现最新赛季 ID: %s (%s)", season_id, latest.get("label", ""))
        return season_id

    def _get_json(self, url: str) -> dict:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(headers=DEFAULT_HEADERS, timeout=self.timeout) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                logger.warning("第 %d 次请求失败 (%s): %s", attempt, url, exc)
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        raise RuntimeError(f"抓取失败（{self.max_retries} 次重试后放弃）: {url}") from last_exc

    def _parse_standings(self, raw: dict) -> StandingsSnapshot:
        """将 PulseAPI 响应解析为 StandingsSnapshot"""
        fetched_at = datetime.now(timezone.utc)

        tables = raw.get("tables", [])
        if not tables:
            raise ValueError("响应中未找到积分榜数据 (tables 为空)")

        # 取第一张积分榜（正常赛季只有一张）
        table_entries = tables[0].get("entries", [])

        standings: dict[int, TeamStanding] = {}
        standings_by_name: dict[str, TeamStanding] = {}

        for entry in table_entries:
            team_info = entry.get("team", {})
            raw_name = team_info.get("name", "")
            short_name = team_info.get("shortName", raw_name)

            # 尝试多个字段映射到标准名
            std_name = (
                self.mapper.resolve(raw_name)
                or self.mapper.resolve(short_name)
                or self.mapper.resolve(team_info.get("club", {}).get("shortName", ""))
            )
            if std_name is None:
                logger.warning("无法映射球队名: '%s' / '%s'", raw_name, short_name)
                std_name = raw_name  # 回退使用原始名称

            stat = entry.get("overall", {})
            rank = entry.get("position", 0)
            points = stat.get("points", 0)

            ts = TeamStanding(
                rank=rank,
                standard_name=std_name,
                played=stat.get("played", 0),
                won=stat.get("won", 0),
                drawn=stat.get("drawn", 0),
                lost=stat.get("lost", 0),
                goals_for=stat.get("goalsFor", 0),
                goals_against=stat.get("goalsAgainst", 0),
                goal_difference=stat.get("goalsDifference", 0),
                points=points,
            )
            standings[rank] = ts
            standings_by_name[std_name] = ts

        # 解析轮次信息（尽力而为）
        matchday = self._parse_matchday(raw)

        return StandingsSnapshot(
            fetched_at=fetched_at,
            source="premierleague.com",
            matchday=matchday,
            standings=standings,
            standings_by_name=standings_by_name,
        )

    def _parse_matchday(self, raw: dict) -> MatchdayInfo | None:
        """尝试从响应中解析轮次信息"""
        try:
            season_info = raw.get("season", {})
            current_matchday = season_info.get("currentMatchday", {})
            if current_matchday:
                gameweek = current_matchday.get("gameweek", {})
                gw_id = gameweek.get("id", 0)
                total = season_info.get("totalMatchdays", 38)
                return MatchdayInfo(
                    latest_completed_matchday=max(0, gw_id - 1),
                    total_matchdays=total,
                    description=f"第 {max(0, gw_id - 1)} 轮",
                )
        except Exception:
            pass

        # 从 tables 里找最后完成的轮次
        try:
            tables = raw.get("tables", [])
            if tables:
                played = tables[0]["entries"][0]["overall"].get("played", 0)
                return MatchdayInfo(
                    latest_completed_matchday=played,
                    total_matchdays=38,
                    description=f"已完赛约 {played} 轮",
                )
        except Exception:
            pass

        return None

    @staticmethod
    def _save_raw(data: dict, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("原始快照已保存: %s", path)

    @staticmethod
    def _save_normalized(snapshot: StandingsSnapshot, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "fetched_at": snapshot.fetched_at.isoformat(),
            "source": snapshot.source,
            "matchday": (
                {
                    "latest_completed": snapshot.matchday.latest_completed_matchday,
                    "total": snapshot.matchday.total_matchdays,
                    "description": snapshot.matchday.description,
                }
                if snapshot.matchday
                else None
            ),
            "standings": [
                {
                    "rank": ts.rank,
                    "team": ts.standard_name,
                    "played": ts.played,
                    "won": ts.won,
                    "drawn": ts.drawn,
                    "lost": ts.lost,
                    "gf": ts.goals_for,
                    "ga": ts.goals_against,
                    "gd": ts.goal_difference,
                    "points": ts.points,
                }
                for ts in sorted(snapshot.standings.values(), key=lambda s: s.rank)
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("规范化快照已保存: %s", path)
