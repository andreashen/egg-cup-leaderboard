"""Pipeline orchestration for fetching, normalizing, and persisting data."""

from datetime import datetime, timezone
import json
from pathlib import Path

from eggcup_leaderboard.config import load_provider_config
from eggcup_leaderboard.models import Metadata, StandingRow
from eggcup_leaderboard.providers.premier_league.client import fetch_json
from eggcup_leaderboard.providers.premier_league.discovery import build_endpoint_urls
from eggcup_leaderboard.providers.premier_league.normalizer import build_metadata, normalize_standings
from eggcup_leaderboard.providers.premier_league.snapshots import write_raw_snapshot


def write_normalized_outputs(
    output_dir: Path,
    standings: list[StandingRow],
    metadata: Metadata,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "standings.json").write_text(
        json.dumps(
            [row.model_dump() for row in standings],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    root = Path.cwd()
    config = load_provider_config(root / "config" / "provider.yml")
    urls = build_endpoint_urls(config.base_url, config.endpoints)
    fetched_at = datetime.now(timezone.utc).isoformat()

    raw_dir = root / "artifacts" / "raw" / config.season
    normalized_dir = root / "artifacts" / "normalized" / config.season

    standings_payload = fetch_json(urls["standings"], config.timeout_seconds)

    write_raw_snapshot(raw_dir, "standings", standings_payload)

    standings = normalize_standings(standings_payload)
    matchweek = standings_payload.get("matchweek")
    latest_round = (
        "Matchweek {number}".format(number=matchweek)
        if isinstance(matchweek, int)
        else None
    )
    metadata = build_metadata(
        season=config.season,
        fetched_at=fetched_at,
        latest_round=latest_round,
    )

    write_normalized_outputs(normalized_dir, standings, metadata)
    return 0
