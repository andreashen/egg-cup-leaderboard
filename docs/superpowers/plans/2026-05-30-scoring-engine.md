# Scoring Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于竞猜输入、上赛季基线和当前官方积分榜的计分引擎，输出玩家总分、排名和分项解释。

**Architecture:** 采用 `inputs -> normalization -> scoring modules -> aggregate results` 的分层结构。输入层负责读取竞猜 CSV、别名表和基线积分榜，计分层分拆为前四、黑马、黑驴三个模块，汇总层统一生成可供页面渲染的结果 JSON。

**Tech Stack:** Python 3.9+、`pytest`、`pydantic`、标准库 `csv/pathlib/json/math`

---

## File Map

- Create: `data/baselines/2024-25_table.csv`
- Create: `data/team_aliases.csv`
- Create: `data/seasons/2025-26.yml`
- Create: `src/eggcup_leaderboard/inputs/__init__.py`
- Create: `src/eggcup_leaderboard/inputs/aliases.py`
- Create: `src/eggcup_leaderboard/inputs/baselines.py`
- Create: `src/eggcup_leaderboard/inputs/predictions.py`
- Create: `src/eggcup_leaderboard/scoring/__init__.py`
- Create: `src/eggcup_leaderboard/scoring/common.py`
- Create: `src/eggcup_leaderboard/scoring/models.py`
- Create: `src/eggcup_leaderboard/scoring/top_four.py`
- Create: `src/eggcup_leaderboard/scoring/upsets.py`
- Create: `src/eggcup_leaderboard/scoring/engine.py`
- Create: `tests/fixtures/scoring/baseline_table.csv`
- Create: `tests/fixtures/scoring/team_aliases.csv`
- Create: `tests/fixtures/scoring/predictions.csv`
- Create: `tests/test_aliases.py`
- Create: `tests/test_predictions.py`
- Create: `tests/test_top_four.py`
- Create: `tests/test_upsets.py`
- Create: `tests/test_scoring_engine.py`
- Modify: `README.md`

### Task 1: 静态输入与领域模型

**Files:**
- Create: `data/baselines/2024-25_table.csv`
- Create: `data/team_aliases.csv`
- Create: `data/seasons/2025-26.yml`
- Create: `src/eggcup_leaderboard/scoring/models.py`
- Create: `tests/test_predictions.py`

- [ ] **Step 1: 写一个失败的领域模型测试**

```python
from eggcup_leaderboard.scoring.models import PlayerPrediction


def test_player_prediction_keeps_multiple_upset_picks() -> None:
    prediction = PlayerPrediction(
        uid="1",
        nickname="中华小当家",
        top_four=["ars", "mci", "liv", "mun"],
        dark_horses=["mun", "tot"],
        dark_donkeys=["bre", "bou"],
    )

    assert prediction.dark_horses == ["mun", "tot"]
    assert prediction.dark_donkeys == ["bre", "bou"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_predictions.py::test_player_prediction_keeps_multiple_upset_picks -v`
Expected: FAIL with `ModuleNotFoundError` for `eggcup_leaderboard.scoring`

- [ ] **Step 3: 建立最小静态输入与模型**

```csv
rank,team_name,team_id,points,is_promoted
1,利物浦,liv,84,false
2,阿森纳,ars,74,false
3,曼城,mci,71,false
4,切尔西,che,69,false
5,纽卡斯尔联,new,66,false
6,阿斯顿维拉,avl,66,false
7,诺丁汉森林,nfo,65,false
8,布莱顿,bha,61,false
9,伯恩茅斯,bou,56,false
10,布伦特福德,bre,56,false
11,富勒姆,ful,54,false
12,水晶宫,cry,53,false
13,埃弗顿,eve,48,false
14,西汉姆联,whu,43,false
15,曼联,mun,42,false
16,狼队,wol,42,false
17,托特纳姆热刺,tot,38,false
18,利兹联,lee,,true
19,伯恩利,bur,,true
20,桑德兰,sun,,true
```

```csv
team_id,canonical_name,alias
ars,阿森纳,阿森纳
ars,阿森纳,Arsenal
ars,阿森纳,ARS
mci,曼城,曼城
mci,曼城,Manchester City
mci,曼城,MCI
liv,利物浦,利物浦
liv,利物浦,Liverpool
mun,曼联,曼联
mun,曼联,Manchester United
tot,托特纳姆热刺,托特纳姆热刺
tot,托特纳姆热刺,热刺
bre,布伦特福德,布伦特福德
bou,伯恩茅斯,伯恩茅斯
lee,利兹联,利兹联
bur,伯恩利,伯恩利
sun,桑德兰,桑德兰
```

```yaml
season: 2025-26
baseline_season: 2024-25
competition: premier-league
promoted_team_ids:
  - lee
  - bur
  - sun
```

```python
from typing import List

from pydantic import BaseModel


class PlayerPrediction(BaseModel):
    uid: str
    nickname: str
    top_four: List[str]
    dark_horses: List[str]
    dark_donkeys: List[str]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_predictions.py::test_player_prediction_keeps_multiple_upset_picks -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add data/baselines/2024-25_table.csv data/team_aliases.csv data/seasons/2025-26.yml src/eggcup_leaderboard/scoring/models.py tests/test_predictions.py
git commit -m "feat: add scoring static inputs and prediction model"
```

### Task 2: 竞猜 CSV 解析与别名归一化

**Files:**
- Create: `src/eggcup_leaderboard/inputs/__init__.py`
- Create: `src/eggcup_leaderboard/inputs/aliases.py`
- Create: `src/eggcup_leaderboard/inputs/predictions.py`
- Create: `tests/fixtures/scoring/team_aliases.csv`
- Create: `tests/fixtures/scoring/predictions.csv`
- Create: `tests/test_aliases.py`
- Modify: `tests/test_predictions.py`

- [ ] **Step 1: 写失败测试，验证别名映射**

```python
from pathlib import Path

from eggcup_leaderboard.inputs.aliases import load_alias_map


def test_load_alias_map_normalizes_case_and_whitespace() -> None:
    alias_map = load_alias_map(Path("tests/fixtures/scoring/team_aliases.csv"))

    assert alias_map["arsenal"] == "ars"
    assert alias_map["阿森纳"] == "ars"
```

- [ ] **Step 2: 写失败测试，验证竞猜 CSV 解析**

```python
from pathlib import Path

from eggcup_leaderboard.inputs.predictions import load_predictions


def test_load_predictions_splits_upset_lists() -> None:
    predictions = load_predictions(
        csv_path=Path("tests/fixtures/scoring/predictions.csv"),
        alias_map={"阿森纳": "ars", "曼城": "mci", "利物浦": "liv", "曼联": "mun", "托特纳姆热刺": "tot", "布伦特福德": "bre", "伯恩茅斯": "bou"},
    )

    assert predictions[0].top_four == ["ars", "mci", "liv", "mun"]
    assert predictions[0].dark_horses == ["mun", "tot"]
```

- [ ] **Step 3: 运行测试确认失败**

Run: `pytest tests/test_aliases.py tests/test_predictions.py -v`
Expected: FAIL with missing `load_alias_map` / `load_predictions`

- [ ] **Step 4: 实现最小别名与竞猜读取**

```csv
team_id,canonical_name,alias
ars,阿森纳,阿森纳
ars,阿森纳,Arsenal
ars,阿森纳,ARSENAL
mci,曼城,曼城
liv,利物浦,利物浦
mun,曼联,曼联
tot,托特纳姆热刺,托特纳姆热刺
bre,布伦特福德,布伦特福德
bou,伯恩茅斯,伯恩茅斯
```

```csv
UID,玩家类型,玩家昵称,英超第1,英超第2,英超第3,英超第4,黑马,黑驴
1,玩家,中华小当家,阿森纳,曼城,利物浦,曼联,曼联、托特纳姆热刺,布伦特福德、伯恩茅斯
```

```python
import csv
from pathlib import Path


def _normalize_alias(value: str) -> str:
    return value.strip().lower()


def load_alias_map(csv_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with csv_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            mapping[_normalize_alias(row["alias"])] = row["team_id"].strip()
    return mapping
```

```python
import csv
from pathlib import Path

from eggcup_leaderboard.scoring.models import PlayerPrediction


def _split_multi_pick(value: str) -> list[str]:
    return [item.strip() for item in value.split("、") if item.strip()]


def load_predictions(csv_path: Path, alias_map: dict[str, str]) -> list[PlayerPrediction]:
    predictions: list[PlayerPrediction] = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["玩家类型"].strip() != "玩家":
                continue
            top_four = [alias_map[row[key].strip().lower()] for key in ["英超第1", "英超第2", "英超第3", "英超第4"]]
            dark_horses = [alias_map[item.strip().lower()] for item in _split_multi_pick(row["黑马"])]
            dark_donkeys = [alias_map[item.strip().lower()] for item in _split_multi_pick(row["黑驴"])]
            predictions.append(
                PlayerPrediction(
                    uid=row["UID"].strip(),
                    nickname=row["玩家昵称"].strip(),
                    top_four=top_four,
                    dark_horses=dark_horses,
                    dark_donkeys=dark_donkeys,
                )
            )
    return predictions
```

- [ ] **Step 5: 运行测试并提交**

Run: `pytest tests/test_aliases.py tests/test_predictions.py -v`
Expected: PASS

```bash
git add src/eggcup_leaderboard/inputs/__init__.py src/eggcup_leaderboard/inputs/aliases.py src/eggcup_leaderboard/inputs/predictions.py tests/fixtures/scoring/team_aliases.csv tests/fixtures/scoring/predictions.csv tests/test_aliases.py tests/test_predictions.py
git commit -m "feat: add prediction csv loader and alias normalization"
```

### Task 3: 基线读取与前四计分

**Files:**
- Create: `src/eggcup_leaderboard/inputs/baselines.py`
- Create: `src/eggcup_leaderboard/scoring/common.py`
- Create: `src/eggcup_leaderboard/scoring/top_four.py`
- Create: `tests/fixtures/scoring/baseline_table.csv`
- Create: `tests/test_top_four.py`

- [ ] **Step 1: 写失败测试，验证前四公式**

```python
from eggcup_leaderboard.scoring.top_four import score_top_four_pick


def test_score_top_four_pick_uses_target_points_gap() -> None:
    score = score_top_four_pick(
        target_rank=4,
        predicted_team_points=70,
        actual_rank_points=60,
    )

    assert score == 50.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_top_four.py::test_score_top_four_pick_uses_target_points_gap -v`
Expected: FAIL with missing `score_top_four_pick`

- [ ] **Step 3: 实现最小基线读取与前四计分**

```csv
rank,team_name,team_id,points,is_promoted
1,利物浦,liv,84,false
2,阿森纳,ars,74,false
3,曼城,mci,71,false
4,切尔西,che,69,false
5,纽卡斯尔联,new,66,false
6,阿斯顿维拉,avl,66,false
15,曼联,mun,42,false
16,狼队,wol,42,false
17,托特纳姆热刺,tot,38,false
18,利兹联,lee,,true
19,伯恩利,bur,,true
20,桑德兰,sun,,true
```

```python
import csv
from pathlib import Path


def load_baseline_rows(csv_path: Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    with csv_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[row["team_id"].strip()] = {
                "rank": int(row["rank"]),
                "points": int(row["points"]) if row["points"] else None,
                "is_promoted": row["is_promoted"].strip().lower() == "true",
            }
    return rows
```

```python
TOP_FOUR_MAX_POINTS = {1: 400, 2: 200, 3: 100, 4: 100}


def score_top_four_pick(target_rank: int, predicted_team_points: int, actual_rank_points: int) -> float:
    base = TOP_FOUR_MAX_POINTS[target_rank]
    return base * (1 - abs(predicted_team_points - actual_rank_points) / 20)
```

- [ ] **Step 4: 补充解释性测试**

```python
from eggcup_leaderboard.scoring.top_four import score_top_four_pick


def test_score_top_four_pick_can_be_negative() -> None:
    score = score_top_four_pick(
        target_rank=1,
        predicted_team_points=10,
        actual_rank_points=90,
    )

    assert score == -1200.0
```

- [ ] **Step 5: 运行测试并提交**

Run: `pytest tests/test_top_four.py -v`
Expected: PASS

```bash
git add src/eggcup_leaderboard/inputs/baselines.py src/eggcup_leaderboard/scoring/common.py src/eggcup_leaderboard/scoring/top_four.py tests/fixtures/scoring/baseline_table.csv tests/test_top_four.py
git commit -m "feat: add baseline loader and top four scoring"
```

### Task 4: 黑马、黑驴与无效竞猜

**Files:**
- Create: `src/eggcup_leaderboard/scoring/upsets.py`
- Create: `tests/test_upsets.py`

- [ ] **Step 1: 写失败测试，验证黑马成功与失败**

```python
from eggcup_leaderboard.scoring.upsets import score_dark_horse_pick


def test_score_dark_horse_pick_rewards_team_points_when_rank_improves_by_three() -> None:
    score = score_dark_horse_pick(
        baseline_rank=15,
        current_rank=5,
        current_points=70,
        fallback_points=60,
    )

    assert score == 70


def test_score_dark_horse_pick_penalizes_fallback_rank_points_when_failed() -> None:
    score = score_dark_horse_pick(
        baseline_rank=15,
        current_rank=13,
        current_points=40,
        fallback_points=45,
    )

    assert score == -45
```

- [ ] **Step 2: 写失败测试，验证黑驴和无效竞猜**

```python
from eggcup_leaderboard.scoring.upsets import is_invalid_dark_donkey_pick, score_dark_donkey_pick


def test_score_dark_donkey_pick_rewards_baseline_points_when_rank_drops_by_three() -> None:
    score = score_dark_donkey_pick(
        baseline_points=66,
        baseline_rank=6,
        current_rank=10,
        current_points=50,
    )

    assert score == 66


def test_invalid_dark_donkey_pick_blocks_promoted_teams() -> None:
    assert is_invalid_dark_donkey_pick(is_promoted=True) is True
```

- [ ] **Step 3: 运行测试确认失败**

Run: `pytest tests/test_upsets.py -v`
Expected: FAIL with missing upset helpers

- [ ] **Step 4: 实现最小黑马/黑驴规则**

```python
def score_dark_horse_pick(
    baseline_rank: int,
    current_rank: int,
    current_points: int,
    fallback_points: int,
) -> int:
    if baseline_rank - current_rank >= 3:
        return current_points
    return -fallback_points


def score_dark_donkey_pick(
    baseline_points: int,
    baseline_rank: int,
    current_rank: int,
    current_points: int,
) -> int:
    if current_rank - baseline_rank >= 3:
        return baseline_points
    return -current_points


def is_invalid_dark_horse_pick(baseline_rank: int) -> bool:
    return baseline_rank <= 3


def is_invalid_dark_donkey_pick(is_promoted: bool) -> bool:
    return is_promoted
```

- [ ] **Step 5: 运行测试并提交**

Run: `pytest tests/test_upsets.py -v`
Expected: PASS

```bash
git add src/eggcup_leaderboard/scoring/upsets.py tests/test_upsets.py
git commit -m "feat: add dark horse and dark donkey scoring"
```

### Task 5: 汇总引擎与规则样例回归

**Files:**
- Create: `src/eggcup_leaderboard/scoring/engine.py`
- Modify: `src/eggcup_leaderboard/scoring/models.py`
- Create: `tests/test_scoring_engine.py`
- Modify: `README.md`

- [ ] **Step 1: 写失败测试，验证规则样例总分**

```python
from eggcup_leaderboard.scoring.engine import rank_players
from eggcup_leaderboard.scoring.models import PlayerPrediction


def test_rank_players_matches_rule_example_total_score() -> None:
    standings = [
        {"team_id": "che", "rank": 1, "points": 90},
        {"team_id": "ars", "rank": 2, "points": 88},
        {"team_id": "liv", "rank": 3, "points": 88},
        {"team_id": "wol", "rank": 4, "points": 75},
        {"team_id": "mun", "rank": 5, "points": 70},
        {"team_id": "mci", "rank": 6, "points": 60},
        {"team_id": "bou", "rank": 13, "points": 30},
    ]
    baseline = {
        "che": {"rank": 4, "points": 69, "is_promoted": False},
        "liv": {"rank": 1, "points": 84, "is_promoted": False},
        "mun": {"rank": 15, "points": 42, "is_promoted": False},
        "ars": {"rank": 2, "points": 74, "is_promoted": False},
        "bou": {"rank": 9, "points": 56, "is_promoted": False},
        "mci": {"rank": 3, "points": 71, "is_promoted": False},
        "wol": {"rank": 16, "points": 42, "is_promoted": False},
    }
    prediction = PlayerPrediction(
        uid="1",
        nickname="小明",
        top_four=["che", "liv", "mun", "ars"],
        dark_horses=["mun", "bou"],
        dark_donkeys=["che", "mci"],
    )

    results = rank_players([prediction], standings=standings, baseline=baseline)

    assert round(results[0].total_score, 2) == 636.0
    assert results[0].rank == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_scoring_engine.py::test_rank_players_matches_rule_example_total_score -v`
Expected: FAIL with missing `rank_players`

- [ ] **Step 3: 扩展结果模型并实现最小汇总引擎**

```python
from typing import Dict, List

from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    label: str
    team_id: str
    score: float
    explanation: str


class PlayerScoreResult(BaseModel):
    uid: str
    nickname: str
    total_score: float
    rank: int
    top_four_scores: List[ScoreBreakdown]
    dark_horse_scores: List[ScoreBreakdown]
    dark_donkey_scores: List[ScoreBreakdown]
```

```python
from eggcup_leaderboard.scoring.models import PlayerScoreResult, ScoreBreakdown
from eggcup_leaderboard.scoring.top_four import score_top_four_pick
from eggcup_leaderboard.scoring.upsets import (
    is_invalid_dark_donkey_pick,
    is_invalid_dark_horse_pick,
    score_dark_donkey_pick,
    score_dark_horse_pick,
)


def _index_standings(rows: list[dict]) -> tuple[dict[str, dict], dict[int, dict]]:
    by_team = {row["team_id"]: row for row in rows}
    by_rank = {row["rank"]: row for row in rows}
    return by_team, by_rank


def rank_players(predictions: list, standings: list[dict], baseline: dict[str, dict]) -> list[PlayerScoreResult]:
    by_team, by_rank = _index_standings(standings)
    results: list[PlayerScoreResult] = []

    for prediction in predictions:
        top_four_scores: list[ScoreBreakdown] = []
        dark_horse_scores: list[ScoreBreakdown] = []
        dark_donkey_scores: list[ScoreBreakdown] = []

        for target_rank, team_id in enumerate(prediction.top_four, start=1):
            predicted_points = by_team[team_id]["points"]
            actual_rank_points = by_rank[target_rank]["points"]
            score = score_top_four_pick(target_rank, predicted_points, actual_rank_points)
            top_four_scores.append(
                ScoreBreakdown(
                    label="top_four",
                    team_id=team_id,
                    score=score,
                    explanation="target_rank={0}, predicted_points={1}, actual_rank_points={2}".format(target_rank, predicted_points, actual_rank_points),
                )
            )

        for team_id in prediction.dark_horses:
            base = baseline[team_id]
            if is_invalid_dark_horse_pick(base["rank"]):
                score = 0
                explanation = "invalid dark horse pick"
            else:
                fallback_rank = base["rank"] - 3
                score = score_dark_horse_pick(
                    baseline_rank=base["rank"],
                    current_rank=by_team[team_id]["rank"],
                    current_points=by_team[team_id]["points"],
                    fallback_points=by_rank[fallback_rank]["points"],
                )
                explanation = "baseline_rank={0}, current_rank={1}".format(base["rank"], by_team[team_id]["rank"])
            dark_horse_scores.append(ScoreBreakdown(label="dark_horse", team_id=team_id, score=score, explanation=explanation))

        for team_id in prediction.dark_donkeys:
            base = baseline[team_id]
            if is_invalid_dark_donkey_pick(base["is_promoted"]):
                score = 0
                explanation = "invalid dark donkey pick"
            else:
                score = score_dark_donkey_pick(
                    baseline_points=base["points"],
                    baseline_rank=base["rank"],
                    current_rank=by_team[team_id]["rank"],
                    current_points=by_team[team_id]["points"],
                )
                explanation = "baseline_rank={0}, current_rank={1}".format(base["rank"], by_team[team_id]["rank"])
            dark_donkey_scores.append(ScoreBreakdown(label="dark_donkey", team_id=team_id, score=score, explanation=explanation))

        total_score = sum(item.score for item in top_four_scores + dark_horse_scores + dark_donkey_scores)
        results.append(
            PlayerScoreResult(
                uid=prediction.uid,
                nickname=prediction.nickname,
                total_score=total_score,
                rank=0,
                top_four_scores=top_four_scores,
                dark_horse_scores=dark_horse_scores,
                dark_donkey_scores=dark_donkey_scores,
            )
        )

    ordered = sorted(results, key=lambda item: item.total_score, reverse=True)
    for index, result in enumerate(ordered, start=1):
        result.rank = index
    return ordered
```

- [ ] **Step 4: 增加 README 入口说明并跑回归**

```markdown
## 计分引擎下一步

- 输入：竞猜 CSV、球队别名表、上赛季基线积分榜、当前 `standings.json`
- 输出：玩家总分、排名、前四明细、黑马明细、黑驴明细
```

Run: `pytest tests/test_scoring_engine.py tests/test_upsets.py tests/test_top_four.py tests/test_aliases.py tests/test_predictions.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/eggcup_leaderboard/scoring/engine.py src/eggcup_leaderboard/scoring/models.py README.md tests/test_scoring_engine.py
git commit -m "feat: add scoring engine and rule example regression"
```
