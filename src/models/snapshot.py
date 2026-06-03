from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TeamStanding:
    """积分榜中某一球队的排名数据"""

    rank: int
    standard_name: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int

    def __repr__(self) -> str:
        return f"TeamStanding(第{self.rank}名 {self.standard_name} {self.points}分)"


@dataclass
class MatchdayInfo:
    """赛程/轮次摘要信息"""

    latest_completed_matchday: int
    total_matchdays: int
    description: str = ""


@dataclass
class StandingsSnapshot:
    """官方积分榜快照"""

    fetched_at: datetime
    source: str
    matchday: MatchdayInfo | None
    # rank -> TeamStanding
    standings: dict[int, TeamStanding] = field(default_factory=dict)
    # standard_name -> TeamStanding（便于查找）
    standings_by_name: dict[str, TeamStanding] = field(default_factory=dict)

    def get_by_rank(self, rank: int) -> TeamStanding | None:
        return self.standings.get(rank)

    def get_by_name(self, name: str) -> TeamStanding | None:
        return self.standings_by_name.get(name)

    def get_points_by_rank(self, rank: int) -> int | None:
        """获取指定名次的球队积分"""
        s = self.standings.get(rank)
        return s.points if s else None

    def get_current_rank(self, name: str) -> int | None:
        """获取球队当前名次"""
        s = self.standings_by_name.get(name)
        return s.rank if s else None
