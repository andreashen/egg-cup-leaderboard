"""球队名称映射单元测试"""

import pytest
from pathlib import Path

from src.utils.team_mapper import TeamMapper

ALIASES_CSV = Path(__file__).parent.parent / "data" / "team_aliases.csv"


@pytest.fixture
def mapper():
    return TeamMapper(ALIASES_CSV)


class TestTeamMapper:
    def test_standard_english_name(self, mapper):
        assert mapper.resolve("Arsenal") == "Arsenal"

    def test_chinese_name(self, mapper):
        assert mapper.resolve("阿森纳") == "Arsenal"
        assert mapper.resolve("曼城") == "Manchester City"
        assert mapper.resolve("曼联") == "Manchester United"

    def test_short_name(self, mapper):
        assert mapper.resolve("man city") == "Manchester City"
        assert mapper.resolve("man united") == "Manchester United"
        assert mapper.resolve("spurs") == "Tottenham Hotspur"

    def test_case_insensitive(self, mapper):
        assert mapper.resolve("ARSENAL") == "Arsenal"
        assert mapper.resolve("chelsea") == "Chelsea"
        assert mapper.resolve("Liverpool FC") == "Liverpool"

    def test_promoted_teams(self, mapper):
        assert mapper.resolve("利兹联") == "Leeds United"
        assert mapper.resolve("伯恩利") == "Burnley"
        assert mapper.resolve("桑德兰") == "Sunderland"

    def test_unknown_team_returns_none(self, mapper):
        assert mapper.resolve("完全不存在的球队") is None

    def test_resolve_or_raise(self, mapper):
        with pytest.raises(ValueError, match="未能识别的球队名称"):
            mapper.resolve_or_raise("假球队")

    def test_wolves_chinese(self, mapper):
        assert mapper.resolve("狼队") == "Wolverhampton Wanderers"

    def test_all_standard_teams_resolvable(self, mapper):
        """所有标准名称本身必须是可映射的"""
        standard_teams = [
            "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
            "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich Town",
            "Leicester City", "Liverpool", "Manchester City", "Manchester United",
            "Newcastle United", "Nottingham Forest", "Southampton", "Tottenham Hotspur",
            "West Ham United", "Wolverhampton Wanderers",
        ]
        for team in standard_teams:
            assert mapper.resolve(team) == team, f"标准名称 '{team}' 应能映射到自身"
