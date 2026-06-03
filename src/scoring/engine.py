"""计分引擎：根据游戏规则计算每位玩家的总分和分项明细"""

import logging
from typing import NamedTuple

from src.models.season import SeasonConfig
from src.models.guess import PlayerGuess
from src.models.snapshot import StandingsSnapshot
from src.models.scoring import (
    Top4ScoreItem,
    DarkHorseScoreItem,
    DarkDonkeyScoreItem,
    PlayerScoreResult,
    InvalidReason,
)

logger = logging.getLogger(__name__)

TOP4_FULL_SCORES = {1: 400, 2: 200, 3: 100, 4: 100}


class ScoringEngine:
    """根据 docs/game_rules.txt 计算积分"""

    def __init__(self, season: SeasonConfig, snapshot: StandingsSnapshot) -> None:
        self.season = season
        self.snapshot = snapshot

    def score_all(self, guesses: list[PlayerGuess]) -> list[PlayerScoreResult]:
        results = [self.score_player(g) for g in guesses]
        # 按总分降序排名
        results.sort(key=lambda r: r.total_score, reverse=True)
        for rank, result in enumerate(results, start=1):
            result.rank = rank
        return results

    def score_player(self, guess: PlayerGuess) -> PlayerScoreResult:
        result = PlayerScoreResult(uid=guess.uid, nickname=guess.nickname)
        result.top4_items = self._score_top4(guess)
        result.dark_horse_items = self._score_dark_horses(guess)
        result.dark_donkey_items = self._score_dark_donkeys(guess)
        result.compute_totals()
        return result

    # ------------------------------------------------------------------
    # 前四计分
    # ------------------------------------------------------------------

    def _score_top4(self, guess: PlayerGuess) -> list[Top4ScoreItem]:
        items = []
        for i, predicted_team in enumerate(guess.top4):
            position = i + 1
            ti = TOP4_FULL_SCORES[position]

            # Pi：玩家预测球队本赛季实际积分
            predicted_standing = self.snapshot.get_by_name(predicted_team)
            if predicted_standing is None:
                raise ValueError(
                    f"积分榜中未找到球队 '{predicted_team}'（玩家 {guess.nickname}）"
                )
            pi = predicted_standing.points

            # Gi：该名次（position）实际球队本赛季积分
            actual_standing = self.snapshot.get_by_rank(position)
            if actual_standing is None:
                raise ValueError(f"积分榜中未找到第 {position} 名数据")
            gi = actual_standing.points
            actual_team = actual_standing.standard_name

            # Xi = Ti × (1 - abs(Pi - Gi) / 20)
            xi = ti * (1 - abs(pi - gi) / 20)

            explanation = (
                f"{predicted_team} 本赛季积 {pi} 分，"
                f"实际第{position}名 {actual_team} 积 {gi} 分，"
                f"|{pi}-{gi}|={abs(pi - gi)}，"
                f"得分={ti}×(1-{abs(pi - gi)}/20)={xi:.1f}"
            )

            items.append(
                Top4ScoreItem(
                    position=position,
                    predicted_team=predicted_team,
                    ti=ti,
                    pi=pi,
                    gi=gi,
                    actual_team_at_position=actual_team,
                    score=xi,
                    explanation=explanation,
                )
            )
        return items

    # ------------------------------------------------------------------
    # 黑马计分
    # ------------------------------------------------------------------

    def _score_dark_horses(self, guess: PlayerGuess) -> list[DarkHorseScoreItem]:
        items = []
        for team in guess.dark_horses:
            item = self._score_one_dark_horse(team, guess.nickname)
            items.append(item)
        return items

    def _score_one_dark_horse(self, team: str, player_name: str) -> DarkHorseScoreItem:
        baseline = self.season.get_baseline(team)
        if baseline is None:
            raise ValueError(f"未找到球队 '{team}' 的上赛季基线数据")

        # 校验：上赛季前三名不能预测为黑马
        if baseline.rank <= 3:
            item = DarkHorseScoreItem(
                team=team,
                last_season_rank=baseline.rank,
                current_season_rank=0,
                rank_improvement=0,
                success=False,
                score=0.0,
                invalid=True,
                invalid_reason=InvalidReason.TOP3_AS_DARK_HORSE,
            )
            item.explanation = f"[无效] {team} 为上赛季第{baseline.rank}名，不能预测为黑马，计0分"
            logger.warning("玩家 %s: %s", player_name, item.explanation)
            return item

        current_standing = self.snapshot.get_by_name(team)
        if current_standing is None:
            raise ValueError(f"积分榜中未找到球队 '{team}'")

        last_rank = baseline.rank
        current_rank = current_standing.rank
        improvement = last_rank - current_rank  # 正数=名次提升

        success = improvement >= 3

        if success:
            score = float(current_standing.points)
            explanation = (
                f"{team} 从上赛季第{last_rank}名升至本赛季第{current_rank}名，"
                f"提升{improvement}名（>=3），黑马成功，"
                f"加本赛季积分={score:.0f}分"
            )
            item = DarkHorseScoreItem(
                team=team,
                last_season_rank=last_rank,
                current_season_rank=current_rank,
                rank_improvement=improvement,
                success=True,
                team_current_points=current_standing.points,
                score=score,
                explanation=explanation,
            )
        else:
            # 失败：扣除（上赛季名次-3）处的本赛季积分
            penalty_rank = last_rank - 3
            penalty_standing = self.snapshot.get_by_rank(penalty_rank)
            if penalty_standing is None:
                raise ValueError(f"积分榜中未找到第 {penalty_rank} 名数据（黑马失败扣分）")
            penalty_points = penalty_standing.points
            score = -float(penalty_points)
            explanation = (
                f"{team} 从上赛季第{last_rank}名至本赛季第{current_rank}名，"
                f"提升{improvement}名（<3），黑马失败，"
                f"扣除第{penalty_rank}名（{penalty_standing.standard_name}）积分={penalty_points}分，"
                f"得分={score:.0f}"
            )
            item = DarkHorseScoreItem(
                team=team,
                last_season_rank=last_rank,
                current_season_rank=current_rank,
                rank_improvement=improvement,
                success=False,
                team_current_points=current_standing.points,
                penalty_rank=penalty_rank,
                penalty_points=penalty_points,
                score=score,
                explanation=explanation,
            )

        return item

    # ------------------------------------------------------------------
    # 黑驴计分
    # ------------------------------------------------------------------

    def _score_dark_donkeys(self, guess: PlayerGuess) -> list[DarkDonkeyScoreItem]:
        items = []
        for team in guess.dark_donkeys:
            item = self._score_one_dark_donkey(team, guess.nickname)
            items.append(item)
        return items

    def _score_one_dark_donkey(self, team: str, player_name: str) -> DarkDonkeyScoreItem:
        baseline = self.season.get_baseline(team)
        if baseline is None:
            raise ValueError(f"未找到球队 '{team}' 的上赛季基线数据")

        # 校验：升班马不能预测为黑驴
        if baseline.is_promoted:
            item = DarkDonkeyScoreItem(
                team=team,
                last_season_rank=baseline.rank,
                current_season_rank=0,
                rank_drop=0,
                success=False,
                score=0.0,
                invalid=True,
                invalid_reason=InvalidReason.PROMOTED_AS_DARK_DONKEY,
            )
            item.explanation = f"[无效] {team} 为升班马，不能预测为黑驴，计0分"
            logger.warning("玩家 %s: %s", player_name, item.explanation)
            return item

        current_standing = self.snapshot.get_by_name(team)
        if current_standing is None:
            raise ValueError(f"积分榜中未找到球队 '{team}'")

        last_rank = baseline.rank
        current_rank = current_standing.rank
        rank_drop = current_rank - last_rank  # 正数=名次下降

        success = rank_drop >= 3

        if success:
            score = float(baseline.points)
            explanation = (
                f"{team} 从上赛季第{last_rank}名降至本赛季第{current_rank}名，"
                f"下降{rank_drop}名（>=3），黑驴成功，"
                f"加上赛季积分={score:.0f}分"
            )
            item = DarkDonkeyScoreItem(
                team=team,
                last_season_rank=last_rank,
                current_season_rank=current_rank,
                rank_drop=rank_drop,
                success=True,
                team_last_points=baseline.points,
                team_current_points=current_standing.points,
                score=score,
                explanation=explanation,
            )
        else:
            score = -float(current_standing.points)
            explanation = (
                f"{team} 从上赛季第{last_rank}名至本赛季第{current_rank}名，"
                f"下降{rank_drop}名（<3），黑驴失败，"
                f"扣除本赛季积分={current_standing.points}分，"
                f"得分={score:.0f}"
            )
            item = DarkDonkeyScoreItem(
                team=team,
                last_season_rank=last_rank,
                current_season_rank=current_rank,
                rank_drop=rank_drop,
                success=False,
                team_last_points=baseline.points,
                team_current_points=current_standing.points,
                score=score,
                explanation=explanation,
            )

        return item
