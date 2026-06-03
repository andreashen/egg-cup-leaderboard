from dataclasses import dataclass, field


@dataclass
class PlayerGuess:
    """玩家竞猜"""

    uid: str
    nickname: str
    # 前四预测：index 0=第1名预测，index 3=第4名预测
    top4: list[str] = field(default_factory=list)
    # 黑马列表（标准球队名）
    dark_horses: list[str] = field(default_factory=list)
    # 黑驴列表（标准球队名）
    dark_donkeys: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"PlayerGuess({self.nickname}, "
            f"前四={self.top4}, "
            f"黑马={self.dark_horses}, "
            f"黑驴={self.dark_donkeys})"
        )
