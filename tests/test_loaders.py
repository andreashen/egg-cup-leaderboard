"""数据加载器单元测试"""

import csv
import tempfile
from pathlib import Path

import pytest

from src.utils.team_mapper import TeamMapper
from src.utils.loaders import load_season_config, load_guesses, load_baselines

ALIASES_CSV = Path(__file__).parent.parent / "data" / "team_aliases.csv"
SEASON_YML = Path(__file__).parent.parent / "data" / "seasons" / "2025-26.yml"
BASELINES_CSV = Path(__file__).parent.parent / "data" / "baselines" / "2024-25_table.csv"


class TestLoadSeasonConfig:
    def test_load_season(self):
        config = load_season_config(SEASON_YML, BASELINES_CSV)
        assert config.season_id == "2025-26"
        assert len(config.teams) == 20
        assert len(config.baselines) == 20

    def test_promoted_teams_in_baselines(self):
        config = load_season_config(SEASON_YML, BASELINES_CSV)
        # 升班马应标记为 is_promoted
        for team in ["Leeds United", "Burnley", "Sunderland"]:
            bl = config.get_baseline(team)
            assert bl is not None
            assert bl.is_promoted is True, f"{team} 应标记为升班马"

    def test_promoted_rank_mapping(self):
        config = load_season_config(SEASON_YML, BASELINES_CSV)
        assert config.baselines["Leeds United"].rank == 18
        assert config.baselines["Burnley"].rank == 19
        assert config.baselines["Sunderland"].rank == 20

    def test_regular_team_baseline(self):
        config = load_season_config(SEASON_YML, BASELINES_CSV)
        bl = config.get_baseline("Liverpool")
        assert bl is not None
        assert bl.rank == 1
        assert bl.points == 84
        assert bl.is_promoted is False


class TestLoadGuesses:
    def _write_csv(self, tmpdir, rows):
        p = tmpdir / "guesses.csv"
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["UID", "玩家类型", "玩家昵称", "英超第1", "英超第2", "英超第3", "英超第4", "黑马", "黑驴"])
            for row in rows:
                w.writerow(row)
        return p

    def test_basic_load(self, tmp_path):
        mapper = TeamMapper(ALIASES_CSV)
        p = self._write_csv(tmp_path, [
            ["1", "玩家", "测试玩家", "Arsenal", "Chelsea", "Liverpool", "Manchester City", "Bournemouth", "Everton"],
        ])
        guesses = load_guesses(p, mapper)
        assert len(guesses) == 1
        assert guesses[0].nickname == "测试玩家"
        assert guesses[0].top4[0] == "Arsenal"
        assert guesses[0].dark_horses == ["Bournemouth"]
        assert guesses[0].dark_donkeys == ["Everton"]

    def test_skip_non_player(self, tmp_path):
        mapper = TeamMapper(ALIASES_CSV)
        p = self._write_csv(tmp_path, [
            ["1", "玩家", "正式玩家", "Arsenal", "Chelsea", "Liverpool", "Manchester City", "", ""],
            ["2", "管理员", "管理员", "Arsenal", "Chelsea", "Liverpool", "Manchester City", "", ""],
        ])
        guesses = load_guesses(p, mapper)
        assert len(guesses) == 1
        assert guesses[0].nickname == "正式玩家"

    def test_chinese_team_names(self, tmp_path):
        mapper = TeamMapper(ALIASES_CSV)
        p = self._write_csv(tmp_path, [
            ["1", "玩家", "中文玩家", "阿森纳", "曼城", "利物浦", "曼联", "曼联、托特纳姆热刺", "布伦特福德、伯恩茅斯"],
        ])
        guesses = load_guesses(p, mapper)
        g = guesses[0]
        assert g.top4 == ["Arsenal", "Manchester City", "Liverpool", "Manchester United"]
        assert g.dark_horses == ["Manchester United", "Tottenham Hotspur"]
        assert g.dark_donkeys == ["Brentford", "Bournemouth"]

    def test_example_csv(self):
        """验证项目示例 CSV 可正常加载"""
        mapper = TeamMapper(ALIASES_CSV)
        p = Path(__file__).parent.parent / "data" / "guess_example.csv"
        guesses = load_guesses(p, mapper)
        assert len(guesses) == 1
        assert guesses[0].nickname == "中华小当家"
