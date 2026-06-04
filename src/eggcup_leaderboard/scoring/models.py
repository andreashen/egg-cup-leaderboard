from typing import List

from pydantic import BaseModel


class PlayerPrediction(BaseModel):
    uid: str
    nickname: str
    top_four: List[str]
    dark_horses: List[str]
    dark_donkeys: List[str]


class ScoreBreakdown(BaseModel):
    label: str
    team_id: str
    score: float
    explanation: str


class PlayerScoreResult(BaseModel):
    uid: str
    nickname: str
    total_score: float
    rank: int
    top_four_scores: List[ScoreBreakdown]
    dark_horse_scores: List[ScoreBreakdown]
    dark_donkey_scores: List[ScoreBreakdown]
