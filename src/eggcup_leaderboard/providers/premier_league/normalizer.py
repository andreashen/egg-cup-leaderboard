from typing import Any, Dict, List, Optional

from eggcup_leaderboard.errors import NormalizeError
from eggcup_leaderboard.models import Metadata, StandingRow


def normalize_standings(payload: Dict[str, Any]) -> List[StandingRow]:
    try:
        entries = payload["tables"][0]["entries"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NormalizeError("standings payload missing tables[0].entries") from exc

    rows: List[StandingRow] = []
    for entry in entries:
        try:
            club = entry["team"]
            overall = entry["overall"]
            row = StandingRow(
                team_id=str(club["abbr"]).lower(),
                team_name=club["name"],
                rank=overall["position"],
                points=overall["points"],
                played=overall["played"],
                won=overall["won"],
                drawn=overall["drawn"],
                lost=overall["lost"],
                goal_difference=overall["goalsFor"] - overall["goalsAgainst"],
            )
        except (KeyError, TypeError) as exc:
            raise NormalizeError("invalid standings entry") from exc
        rows.append(row)
    return rows


def build_metadata(
    season: str,
    fetched_at: str,
    latest_round: Optional[str],
) -> Metadata:
    return Metadata(
        season=season,
        source="premierleague.com",
        fetched_at=fetched_at,
        latest_round=latest_round,
        match_progress=latest_round,
    )
