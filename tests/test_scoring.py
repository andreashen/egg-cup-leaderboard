"""
计分引擎单元测试
使用 game_rules.txt 中的示例数据验证计算结果
"""

import pytest
from datetime import datetime, timezone

from src.models.season import SeasonConfig, TeamBaseline
from src.models.guess import PlayerGuess
from src.models.snapshot import StandingsSnapshot, TeamStanding, MatchdayInfo
from src.scoring.engine import ScoringEngine


# ------------------------------------------------------------------
# 测试固件：根据 game_rules.txt 示例构建的场景
# ------------------------------------------------------------------
# 假设25/26赛季英超部分结果为：
# 1-切尔西90分，2-阿森纳88分，3-利物浦88分，4-狼队75分，5-曼联70分，6-曼城60分
#
# 2024/25赛季基线（部分）：
#   1-利物浦84, 2-阿森纳74, 3-曼城71, 4-切尔西69,
#   9-伯恩茅斯56, 15-曼联42

def _make_snapshot() -> StandingsSnapshot:
    rows = [
        (1, "Chelsea", 90),
        (2, "Arsenal", 88),
        (3, "Liverpool", 88),
        (4, "Wolverhampton Wanderers", 75),
        (5, "Manchester United", 70),
        (6, "Manchester City", 60),
        (7, "Tottenham Hotspur", 55),
        (8, "Newcastle United", 54),
        (9, "Bournemouth", 50),
        (10, "Brighton", 48),
        (11, "Brentford", 45),
        (12, "Crystal Palace", 42),
        (13, "Aston Villa", 40),
        (14, "Everton", 38),
        (15, "Fulham", 36),
        (16, "Nottingham Forest", 34),
        (17, "West Ham United", 30),
        (18, "Southampton", 25),
        (19, "Leicester City", 20),
        (20, "Ipswich Town", 18),
    ]
    standings = {}
    standings_by_name = {}
    for rank, name, pts in rows:
        ts = TeamStanding(
            rank=rank, standard_name=name, played=38,
            won=0, drawn=0, lost=0, goals_for=0, goals_against=0,
            goal_difference=0, points=pts,
        )
        standings[rank] = ts
        standings_by_name[name] = ts

    return StandingsSnapshot(
        fetched_at=datetime(2026, 5, 25, tzinfo=timezone.utc),
        source="test",
        matchday=MatchdayInfo(38, 38, "第38轮"),
        standings=standings,
        standings_by_name=standings_by_name,
    )


def _make_season() -> SeasonConfig:
    baselines = {
        "Liverpool": TeamBaseline("Liverpool", 1, 84),
        "Arsenal": TeamBaseline("Arsenal", 2, 74),
        "Manchester City": TeamBaseline("Manchester City", 3, 71),
        "Chelsea": TeamBaseline("Chelsea", 4, 69),
        "Newcastle United": TeamBaseline("Newcastle United", 5, 66),
        "Aston Villa": TeamBaseline("Aston Villa", 6, 66),
        "Nottingham Forest": TeamBaseline("Nottingham Forest", 7, 65),
        "Brighton": TeamBaseline("Brighton", 8, 61),
        "Bournemouth": TeamBaseline("Bournemouth", 9, 56),
        "Brentford": TeamBaseline("Brentford", 10, 56),
        "Fulham": TeamBaseline("Fulham", 11, 54),
        "Crystal Palace": TeamBaseline("Crystal Palace", 12, 53),
        "Everton": TeamBaseline("Everton", 13, 48),
        "West Ham United": TeamBaseline("West Ham United", 14, 43),
        "Manchester United": TeamBaseline("Manchester United", 15, 42),
        "Wolverhampton Wanderers": TeamBaseline("Wolverhampton Wanderers", 16, 42),
        "Tottenham Hotspur": TeamBaseline("Tottenham Hotspur", 17, 38),
        "Leeds United": TeamBaseline("Leeds United", 18, 0, is_promoted=True),
        "Burnley": TeamBaseline("Burnley", 19, 0, is_promoted=True),
        "Sunderland": TeamBaseline("Sunderland", 20, 0, is_promoted=True),
    }
    return SeasonConfig(
        season_id="2025-26",
        season_name="2025/26 Premier League",
        baseline_season="2024-25",
        promoted_teams={"Leeds United": 18, "Burnley": 19, "Sunderland": 20},
        baselines=baselines,
    )


# ------------------------------------------------------------------
# 前四计分
# ------------------------------------------------------------------

class TestTop4Scoring:
    """前四计分规则验证"""

    def setup_method(self):
        self.snapshot = _make_snapshot()
        self.season = _make_season()
        self.engine = ScoringEngine(self.season, self.snapshot)

    def test_exact_match_position_1(self):
        """预测切尔西第1名，切尔西确实是第1名，|90-90|=0, 400×1=400"""
        guess = PlayerGuess("1", "Test", top4=["Chelsea", "Liverpool", "Arsenal", "Wolverhampton Wanderers"])
        result = self.engine.score_player(guess)
        item = result.top4_items[0]
        assert item.score == pytest.approx(400.0)

    def test_zero_point_diff_position_2(self):
        """利物浦预测第2名，利物浦本赛季88分，第2名阿森纳88分，|0|/20=0, 200×1=200"""
        guess = PlayerGuess("1", "Test", top4=["Chelsea", "Liverpool", "Arsenal", "Wolverhampton Wanderers"])
        result = self.engine.score_player(guess)
        item = result.top4_items[1]
        assert item.pi == 88
        assert item.gi == 88
        assert item.score == pytest.approx(200.0)

    def test_game_rules_example_top4(self):
        """验证 game_rules.txt 示例：小明预测切尔西/利物浦/曼联/阿森纳"""
        guess = PlayerGuess(
            "1", "小明",
            top4=["Chelsea", "Liverpool", "Manchester United", "Arsenal"],
            dark_horses=["Manchester United", "Bournemouth"],
            dark_donkeys=["Chelsea", "Manchester City"],
        )
        result = self.engine.score_player(guess)

        # 前四各项得分
        # 切尔西第1：Pi=90,Gi=90,400×(1-0/20)=400
        assert result.top4_items[0].score == pytest.approx(400.0)
        # 利物浦第2：Pi=88,Gi=88,200×(1-0/20)=200
        assert result.top4_items[1].score == pytest.approx(200.0)
        # 曼联第3：Pi=70,Gi=88,100×(1-18/20)=10
        assert result.top4_items[2].score == pytest.approx(10.0)
        # 阿森纳第4：Pi=88,Gi=75,100×(1-13/20)=35
        assert result.top4_items[3].score == pytest.approx(35.0)

    def test_negative_score_possible(self):
        """Xi 允许为负分"""
        # Pi=18(第20名伊普斯维奇), Gi=90(第1名切尔西), 差距72, 100×(1-72/20)=-260
        guess = PlayerGuess("1", "Test", top4=["Ipswich Town", "Arsenal", "Liverpool", "Wolverhampton Wanderers"])
        result = self.engine.score_player(guess)
        item = result.top4_items[0]
        assert item.score < 0


# ------------------------------------------------------------------
# 黑马计分
# ------------------------------------------------------------------

class TestDarkHorseScoring:
    def setup_method(self):
        self.snapshot = _make_snapshot()
        self.season = _make_season()
        self.engine = ScoringEngine(self.season, self.snapshot)

    def test_dark_horse_success(self):
        """曼联上赛季第15名，本赛季第5名，提升10名>=3，黑马成功，加70分"""
        guess = PlayerGuess("1", "Test", top4=["Chelsea","Arsenal","Liverpool","Wolverhampton Wanderers"],
                            dark_horses=["Manchester United"])
        result = self.engine.score_player(guess)
        item = result.dark_horse_items[0]
        assert item.success is True
        assert item.score == pytest.approx(70.0)  # 曼联本赛季70分

    def test_dark_horse_failure_deduction(self):
        """伯恩茅斯上赛季第9名，本赛季第9名，提升0<3，失败
        扣除第(9-3)=6名积分=60分"""
        guess = PlayerGuess("1", "Test", top4=["Chelsea","Arsenal","Liverpool","Wolverhampton Wanderers"],
                            dark_horses=["Bournemouth"])
        result = self.engine.score_player(guess)
        item = result.dark_horse_items[0]
        assert item.success is False
        assert item.penalty_rank == 6
        assert item.penalty_points == 60
        assert item.score == pytest.approx(-60.0)

    def test_dark_horse_invalid_top3(self):
        """上赛季前三名（Liverpool=1, Arsenal=2, Manchester City=3）预测为黑马→无效，计0分"""
        for team in ["Liverpool", "Arsenal", "Manchester City"]:
            guess = PlayerGuess("1", "Test", top4=["Chelsea","Brentford","Everton","Fulham"],
                                dark_horses=[team])
            result = self.engine.score_player(guess)
            item = result.dark_horse_items[0]
            assert item.invalid is True
            assert item.score == pytest.approx(0.0), f"{team} 应为无效黑马"

    def test_game_rules_example_dark_horse(self):
        """验证示例：曼联成功+70，伯恩茅斯失败-60"""
        guess = PlayerGuess(
            "1", "小明",
            top4=["Chelsea", "Liverpool", "Manchester United", "Arsenal"],
            dark_horses=["Manchester United", "Bournemouth"],
            dark_donkeys=["Chelsea", "Manchester City"],
        )
        result = self.engine.score_player(guess)
        # 曼联黑马成功
        assert result.dark_horse_items[0].score == pytest.approx(70.0)
        # 伯恩茅斯黑马失败
        assert result.dark_horse_items[1].score == pytest.approx(-60.0)


# ------------------------------------------------------------------
# 黑驴计分
# ------------------------------------------------------------------

class TestDarkDonkeyScoring:
    def setup_method(self):
        self.snapshot = _make_snapshot()
        self.season = _make_season()
        self.engine = ScoringEngine(self.season, self.snapshot)

    def test_dark_donkey_success(self):
        """曼城上赛季第3名，本赛季第6名，下降3名>=3，黑驴成功，加上赛季积分71"""
        guess = PlayerGuess("1", "Test", top4=["Chelsea","Arsenal","Liverpool","Wolverhampton Wanderers"],
                            dark_donkeys=["Manchester City"])
        result = self.engine.score_player(guess)
        item = result.dark_donkey_items[0]
        assert item.success is True
        assert item.score == pytest.approx(71.0)

    def test_dark_donkey_failure_deduction(self):
        """切尔西上赛季第4名，本赛季第1名（上升3名），下降-3<3，黑驴失败，扣本赛季90分"""
        guess = PlayerGuess("1", "Test", top4=["Chelsea","Arsenal","Liverpool","Wolverhampton Wanderers"],
                            dark_donkeys=["Chelsea"])
        result = self.engine.score_player(guess)
        item = result.dark_donkey_items[0]
        assert item.success is False
        assert item.score == pytest.approx(-90.0)

    def test_dark_donkey_invalid_promoted(self):
        """升班马不能预测为黑驴→无效，计0分"""
        for team in ["Leeds United", "Burnley", "Sunderland"]:
            guess = PlayerGuess("1", "Test", top4=["Chelsea","Arsenal","Liverpool","Wolverhampton Wanderers"],
                                dark_donkeys=[team])
            result = self.engine.score_player(guess)
            item = result.dark_donkey_items[0]
            assert item.invalid is True
            assert item.score == pytest.approx(0.0), f"{team} 应为无效黑驴"

    def test_game_rules_example_dark_donkey(self):
        """验证示例：切尔西失败-90，曼城成功+71"""
        guess = PlayerGuess(
            "1", "小明",
            top4=["Chelsea", "Liverpool", "Manchester United", "Arsenal"],
            dark_horses=["Manchester United", "Bournemouth"],
            dark_donkeys=["Chelsea", "Manchester City"],
        )
        result = self.engine.score_player(guess)
        assert result.dark_donkey_items[0].score == pytest.approx(-90.0)
        assert result.dark_donkey_items[1].score == pytest.approx(71.0)


# ------------------------------------------------------------------
# 完整总分验证
# ------------------------------------------------------------------

class TestTotalScore:
    def test_game_rules_example_total(self):
        """验证 game_rules.txt 示例总分 = 636 分"""
        snapshot = _make_snapshot()
        season = _make_season()
        engine = ScoringEngine(season, snapshot)

        guess = PlayerGuess(
            "1", "小明",
            top4=["Chelsea", "Liverpool", "Manchester United", "Arsenal"],
            dark_horses=["Manchester United", "Bournemouth"],
            dark_donkeys=["Chelsea", "Manchester City"],
        )
        result = engine.score_player(guess)

        # 前四: 400 + 200 + 10 + 35 = 645
        assert result.top4_total == pytest.approx(645.0)
        # 黑马: 70 - 60 = 10
        assert result.dark_horse_total == pytest.approx(10.0)
        # 黑驴: -90 + 71 = -19
        assert result.dark_donkey_total == pytest.approx(-19.0)
        # 总分: 645 + 10 - 19 = 636
        assert result.total_score == pytest.approx(636.0)

    def test_ranking_order(self):
        """多玩家时按总分降序排名"""
        snapshot = _make_snapshot()
        season = _make_season()
        engine = ScoringEngine(season, snapshot)

        guesses = [
            PlayerGuess("1", "低分玩家", top4=["Ipswich Town", "Leicester City", "Southampton", "West Ham United"]),
            PlayerGuess("2", "高分玩家", top4=["Chelsea", "Arsenal", "Liverpool", "Wolverhampton Wanderers"]),
        ]
        results = engine.score_all(guesses)
        assert results[0].nickname == "高分玩家"
        assert results[0].rank == 1
        assert results[1].nickname == "低分玩家"
        assert results[1].rank == 2
