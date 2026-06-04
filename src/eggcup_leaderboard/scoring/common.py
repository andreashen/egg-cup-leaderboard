from typing import Dict, Optional, TypedDict


class BaselineRow(TypedDict):
    rank: int
    points: Optional[int]
    is_promoted: bool


BaselineTable = Dict[str, BaselineRow]

TOP_FOUR_MAX_POINTS = {1: 400, 2: 200, 3: 100, 4: 100}
