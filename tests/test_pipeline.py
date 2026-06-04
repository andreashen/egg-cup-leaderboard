import json
from pathlib import Path

from eggcup_leaderboard.models import Metadata, StandingRow
from eggcup_leaderboard.pipeline import write_normalized_outputs


def test_write_normalized_outputs_creates_json_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "normalized"
    standings = [
        StandingRow(
            team_id="liv",
            team_name="Liverpool",
            rank=1,
            points=84,
            played=38,
            won=25,
            drawn=9,
            lost=4,
            goal_difference=45,
        )
    ]
    metadata = Metadata(
        season="2025-26",
        source="premierleague.com",
        fetched_at="2026-05-29T12:00:00Z",
        latest_round="Matchweek 38",
        match_progress="Matchweek 38",
    )

    write_normalized_outputs(
        output_dir=output_dir,
        standings=standings,
        metadata=metadata,
    )

    standings_payload = json.loads(
        (output_dir / "standings.json").read_text(encoding="utf-8")
    )
    metadata_payload = json.loads(
        (output_dir / "metadata.json").read_text(encoding="utf-8")
    )

    assert standings_payload[0]["team_name"] == "Liverpool"
    assert metadata_payload["latest_round"] == "Matchweek 38"


def test_cli_main_delegates_to_pipeline(monkeypatch) -> None:
    from eggcup_leaderboard import cli

    called = {"value": False}

    def fake_run_pipeline() -> int:
        called["value"] = True
        return 0

    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)

    assert cli.main() == 0
    assert called["value"] is True
