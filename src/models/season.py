from dataclasses import dataclass, field


@dataclass
class TeamBaseline:
    """上赛季球队基准数据"""

    standard_name: str
    rank: int
    points: int
    is_promoted: bool = False

    def __repr__(self) -> str:
        tag = " [升班马]" if self.is_promoted else ""
        return f"TeamBaseline({self.standard_name}, 第{self.rank}名, {self.points}分{tag})"


@dataclass
class SeasonConfig:
    """赛季配置"""

    season_id: str
    season_name: str
    baseline_season: str
    teams: list[str] = field(default_factory=list)
    # 升班马映射：标准名 -> 基准英超名次（18/19/20）
    promoted_teams: dict[str, int] = field(default_factory=dict)
    # 上赛季积分榜基准：标准名 -> TeamBaseline
    baselines: dict[str, TeamBaseline] = field(default_factory=dict)

    def is_promoted_team(self, team: str) -> bool:
        return team in self.promoted_teams

    def get_baseline(self, team: str) -> TeamBaseline | None:
        return self.baselines.get(team)
