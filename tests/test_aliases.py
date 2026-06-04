from pathlib import Path

from eggcup_leaderboard.inputs.aliases import load_alias_map, normalize_alias


def test_normalize_alias_trims_whitespace_and_case() -> None:
    assert normalize_alias(" Arsenal ") == "arsenal"


def test_load_alias_map_normalizes_case_and_whitespace() -> None:
    alias_map = load_alias_map(Path("tests/fixtures/scoring/team_aliases.csv"))

    assert alias_map["arsenal"] == "ars"
    assert alias_map["阿森纳"] == "ars"
