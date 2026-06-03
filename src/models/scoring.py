from dataclasses import dataclass, field
from enum import Enum


class InvalidReason(str, Enum):
    TOP3_AS_DARK_HORSE = "上赛季前三名不能预测为黑马"
    PROMOTED_AS_DARK_DONKEY = "升班马不能预测为黑驴"


@dataclass
class Top4ScoreItem:
    """前四某一名次的计分明细"""

    position: int          # 名次（1-4）
    predicted_team: str    # 玩家预测球队
    ti: int                # 满分
    pi: int                # 玩家预测球队本赛季积分
    gi: int                # 该名次实际球队本赛季积分
    actual_team_at_position: str  # 该名次实际球队
    score: float           # Xi = Ti × (1 - abs(Pi - Gi) / 20)
    explanation: str = ""


@dataclass
class DarkHorseScoreItem:
    """黑马竞猜计分明细"""

    team: str
    last_season_rank: int      # 上赛季名次
    current_season_rank: int   # 本赛季名次
    rank_improvement: int      # 名次提升（上赛季-本赛季，正数=提升）
    success: bool              # 是否黑马成功（提升>=3）
    # 成功：该球队本赛季积分
    team_current_points: int = 0
    # 失败扣分依据：上赛季名次-3 处本赛季积分
    penalty_rank: int = 0      # 上赛季名次-3
    penalty_points: int = 0    # 该名次本赛季积分
    score: float = 0.0
    invalid: bool = False
    invalid_reason: str = ""
    explanation: str = ""


@dataclass
class DarkDonkeyScoreItem:
    """黑驴竞猜计分明细"""

    team: str
    last_season_rank: int
    current_season_rank: int
    rank_drop: int             # 名次下降（本赛季-上赛季，正数=下降）
    success: bool              # 是否黑驴成功（下降>=3）
    # 成功：该球队上赛季积分
    team_last_points: int = 0
    # 失败：扣除该球队本赛季积分
    team_current_points: int = 0
    score: float = 0.0
    invalid: bool = False
    invalid_reason: str = ""
    explanation: str = ""


@dataclass
class PlayerScoreResult:
    """玩家总计分结果"""

    uid: str
    nickname: str
    rank: int = 0
    total_score: float = 0.0
    top4_total: float = 0.0
    dark_horse_total: float = 0.0
    dark_donkey_total: float = 0.0
    top4_items: list[Top4ScoreItem] = field(default_factory=list)
    dark_horse_items: list[DarkHorseScoreItem] = field(default_factory=list)
    dark_donkey_items: list[DarkDonkeyScoreItem] = field(default_factory=list)

    def compute_totals(self) -> None:
        self.top4_total = sum(item.score for item in self.top4_items)
        self.dark_horse_total = sum(item.score for item in self.dark_horse_items)
        self.dark_donkey_total = sum(item.score for item in self.dark_donkey_items)
        self.total_score = self.top4_total + self.dark_horse_total + self.dark_donkey_total
