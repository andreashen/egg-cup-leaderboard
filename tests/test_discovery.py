from pathlib import Path
import json

from eggcup_leaderboard.providers.premier_league.discovery import build_endpoint_urls
from eggcup_leaderboard.providers.premier_league.snapshots import write_raw_snapshot


def test_build_endpoint_urls_joins_base_url_and_paths() -> None:
    urls = build_endpoint_urls(
        base_url="https://www.premierleague.com/",
        endpoints={"standings": "/api/standings", "fixtures": "api/fixtures"},
    )

    assert urls == {
        "standings": "https://www.premierleague.com/api/standings",
        "fixtures": "https://www.premierleague.com/api/fixtures",
    }


def test_write_raw_snapshot_creates_formatted_json_file(tmp_path: Path) -> None:
    output_path = write_raw_snapshot(
        output_dir=tmp_path / "raw",
        name="standings",
        payload={"tables": [{"entries": []}]},
    )

    assert output_path == tmp_path / "raw" / "standings.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == {
        "tables": [{"entries": []}]
    }
