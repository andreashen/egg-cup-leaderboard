from typing import Optional

from pydantic import BaseModel


class StandingRow(BaseModel):
    team_id: str
    team_name: str
    rank: int
    points: int
    played: int
    won: int
    drawn: int
    lost: int
    goal_difference: int


class Metadata(BaseModel):
    season: str
    source: str
    fetched_at: str
    latest_round: Optional[str] = None
    match_progress: Optional[str] = None
