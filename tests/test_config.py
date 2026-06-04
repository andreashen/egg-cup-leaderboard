from pathlib import Path

from eggcup_leaderboard.config import load_provider_config


def test_load_provider_config_reads_timeout_and_endpoints(tmp_path: Path) -> None:
    config_path = tmp_path / "provider.yml"
    config_path.write_text(
        "season: 2025-26\n"
        "base_url: https://api.example.com\n"
        "timeout_seconds: 10\n"
        "retries: 2\n"
        "endpoints:\n"
        "  standings: /standings/data\n",
        encoding="utf-8",
    )

    config = load_provider_config(config_path)

    assert config.timeout_seconds == 10
    assert config.endpoints["standings"] == "/standings/data"
