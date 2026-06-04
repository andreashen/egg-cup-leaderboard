# Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建第一里程碑的数据链路，实现 `premierleague.com` JSON 数据抓取、规范化和落盘。

**Architecture:** 采用 `provider -> normalizer -> pipeline` 三段式结构。`provider` 负责请求和保存原始响应，`normalizer` 负责转换为内部统一结构，`pipeline` 负责串联流程、输出产物和控制失败退出。

**Tech Stack:** Python 3.9+、`pytest`、`httpx`、`pydantic`、标准库 `pathlib/json/logging`

**Scope Update:** 该计划已根据后续确认收缩为 `standings-only`。当前第一里程碑只保留 `standings + metadata` 数据链路；文档中与 `fixtures` 抓取、规范化、落盘相关的步骤视为后续阶段预留，不属于当前完成标准。

---

## File Map

- Create: `pyproject.toml`
- Create: `src/eggcup_leaderboard/__init__.py`
- Create: `src/eggcup_leaderboard/cli.py`
- Create: `src/eggcup_leaderboard/config.py`
- Create: `src/eggcup_leaderboard/errors.py`
- Create: `src/eggcup_leaderboard/models.py`
- Create: `src/eggcup_leaderboard/pipeline.py`
- Create: `src/eggcup_leaderboard/providers/__init__.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/__init__.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/client.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/discovery.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/normalizer.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/snapshots.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/premier_league/standings_response.json`
- Create: `tests/fixtures/premier_league/fixtures_response.json`
- Create: `tests/test_config.py`
- Create: `tests/test_models.py`
- Create: `tests/test_discovery.py`
- Create: `tests/test_provider_client.py`
- Create: `tests/test_normalizer.py`
- Create: `tests/test_pipeline.py`
- Create: `config/provider.yml`
- Modify: `README.md`
- Create: `artifacts/raw/.gitkeep`
- Create: `artifacts/normalized/.gitkeep`

### Task 1: 项目骨架与测试入口

**Files:**
- Create: `pyproject.toml`
- Create: `src/eggcup_leaderboard/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: 写一个失败的模型测试**

```python
from eggcup_leaderboard.models import Metadata


def test_metadata_defaults_to_empty_match_progress() -> None:
    metadata = Metadata(
        season="2025-26",
        source="premierleague.com",
        fetched_at="2026-05-29T12:00:00Z",
        latest_round=None,
    )

    assert metadata.match_progress is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'eggcup_leaderboard'`

- [ ] **Step 3: 建立最小项目骨架**

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "egg-cup-leaderboard"
version = "0.1.0"
description = "Premier League prediction leaderboard pipeline"
requires-python = ">=3.12"
dependencies = [
  "httpx>=0.27.0",
  "pydantic>=2.7.0",
  "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "pytest-httpx>=0.30.0",
]

[project.scripts]
eggcup-pipeline = "eggcup_leaderboard.cli:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```python
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
```

- [ ] **Step 4: 再跑测试确认进入下一个失败点**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ImportError` pointing to missing `Metadata`

- [ ] **Step 5: 提交**

```bash
git add pyproject.toml src/eggcup_leaderboard/__init__.py tests/conftest.py tests/test_models.py
git commit -m "chore: bootstrap python package skeleton"
```

### Task 2: 内部模型与配置加载

**Files:**
- Create: `src/eggcup_leaderboard/models.py`
- Create: `src/eggcup_leaderboard/config.py`
- Create: `src/eggcup_leaderboard/errors.py`
- Create: `config/provider.yml`
- Modify: `tests/test_models.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 为配置加载写失败测试**

```python
from pathlib import Path

from eggcup_leaderboard.config import load_provider_config


def test_load_provider_config_reads_timeout_and_endpoints(tmp_path: Path) -> None:
    config_path = tmp_path / "provider.yml"
    config_path.write_text(
        "season: 2025-26\n"
        "base_url: https://www.premierleague.com\n"
        "timeout_seconds: 10\n"
        "retries: 2\n"
        "endpoints:\n"
        "  standings: /standings/data\n"
        "  fixtures: /fixtures/data\n",
        encoding="utf-8",
    )

    config = load_provider_config(config_path)

    assert config.timeout_seconds == 10
    assert config.endpoints["standings"] == "/standings/data"
```

- [ ] **Step 2: 运行配置测试确认失败**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ImportError` for missing `load_provider_config`

- [ ] **Step 3: 实现最小模型与配置**

```python
from pydantic import BaseModel


class StandingRow(BaseModel):
    team_id: str
    team_name: str
    rank: int
    points: int
    played: int
    won: int
    drawn: int
    lost: int
    goal_difference: int


class FixtureRow(BaseModel):
    fixture_id: str
    round_label: str | None
    kickoff_at: str | None
    status: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None


class Metadata(BaseModel):
    season: str
    source: str
    fetched_at: str
    latest_round: str | None = None
    match_progress: str | None = None
```

```python
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    season: str
    base_url: str
    timeout_seconds: int = Field(gt=0)
    retries: int = Field(ge=0)
    endpoints: dict[str, str]


def load_provider_config(path: Path) -> ProviderConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProviderConfig.model_validate(data)
```

```python
class PipelineError(RuntimeError):
    """Base pipeline error."""


class DiscoveryError(PipelineError):
    """Raised when provider endpoints are unavailable."""


class NormalizeError(PipelineError):
    """Raised when payload structure is invalid."""
```

```yaml
season: 2025-26
base_url: https://www.premierleague.com
timeout_seconds: 15
retries: 2
endpoints:
  standings: /tables
  fixtures: /fixtures
```

- [ ] **Step 4: 补齐模型测试并确认通过**

```python
from eggcup_leaderboard.models import FixtureRow, Metadata, StandingRow


def test_metadata_defaults_to_empty_match_progress() -> None:
    metadata = Metadata(
        season="2025-26",
        source="premierleague.com",
        fetched_at="2026-05-29T12:00:00Z",
        latest_round=None,
    )

    assert metadata.match_progress is None


def test_standing_row_requires_numeric_points() -> None:
    row = StandingRow(
        team_id="arsenal",
        team_name="Arsenal",
        rank=1,
        points=89,
        played=38,
        won=27,
        drawn=8,
        lost=3,
        goal_difference=48,
    )

    assert row.points == 89


def test_fixture_row_keeps_nullable_scores() -> None:
    fixture = FixtureRow(
        fixture_id="match-1",
        round_label="Matchweek 1",
        kickoff_at="2026-08-15T19:00:00Z",
        status="SCHEDULED",
        home_team="Liverpool",
        away_team="Arsenal",
        home_score=None,
        away_score=None,
    )

    assert fixture.home_score is None
```

- [ ] **Step 5: 跑测试并提交**

Run: `pytest tests/test_models.py tests/test_config.py -v`
Expected: PASS

```bash
git add src/eggcup_leaderboard/models.py src/eggcup_leaderboard/config.py src/eggcup_leaderboard/errors.py config/provider.yml tests/test_models.py tests/test_config.py
git commit -m "feat: add pipeline models and config loader"
```

### Task 3: 发现 JSON 入口并抓取原始响应

**Files:**
- Create: `src/eggcup_leaderboard/providers/__init__.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/__init__.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/discovery.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/client.py`
- Create: `src/eggcup_leaderboard/providers/premier_league/snapshots.py`
- Create: `tests/test_discovery.py`
- Create: `tests/test_provider_client.py`

- [ ] **Step 1: 为入口发现写失败测试**

```python
from eggcup_leaderboard.providers.premier_league.discovery import build_endpoint_urls


def test_build_endpoint_urls_joins_base_url_and_paths() -> None:
    urls = build_endpoint_urls(
        base_url="https://www.premierleague.com",
        endpoints={"standings": "/api/standings", "fixtures": "/api/fixtures"},
    )

    assert urls["standings"] == "https://www.premierleague.com/api/standings"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_discovery.py -v`
Expected: FAIL with `ImportError` for missing `build_endpoint_urls`

- [ ] **Step 3: 实现入口拼接与快照写入**

```python
def build_endpoint_urls(base_url: str, endpoints: dict[str, str]) -> dict[str, str]:
    root = base_url.rstrip("/")
    return {
        name: f"{root}/{path.lstrip('/')}"
        for name, path in endpoints.items()
    }
```

```python
from pathlib import Path
import json


def write_raw_snapshot(output_dir: Path, name: str, payload: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{name}.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target
```

- [ ] **Step 4: 为 HTTP 客户端补测试和最小实现**

```python
import httpx

from eggcup_leaderboard.providers.premier_league.client import fetch_json


def test_fetch_json_returns_payload(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://www.premierleague.com/api/standings",
        json={"tables": []},
    )

    payload = fetch_json(
        url="https://www.premierleague.com/api/standings",
        timeout_seconds=5,
    )

    assert payload == {"tables": []}
```

```python
import httpx

from eggcup_leaderboard.errors import DiscoveryError


def fetch_json(url: str, timeout_seconds: int) -> dict:
    try:
        response = httpx.get(url, timeout=timeout_seconds)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise DiscoveryError(str(exc)) from exc
    return response.json()
```

- [ ] **Step 5: 跑测试并提交**

Run: `pytest tests/test_discovery.py tests/test_provider_client.py -v`
Expected: PASS

```bash
git add src/eggcup_leaderboard/providers src/eggcup_leaderboard/errors.py tests/test_discovery.py tests/test_provider_client.py
git commit -m "feat: add provider discovery and raw fetch client"
```

### Task 4: 规范化 standings、fixtures、metadata

**Files:**
- Create: `src/eggcup_leaderboard/providers/premier_league/normalizer.py`
- Create: `tests/fixtures/premier_league/standings_response.json`
- Create: `tests/fixtures/premier_league/fixtures_response.json`
- Create: `tests/test_normalizer.py`

- [ ] **Step 1: 先写 standings 规范化失败测试**

```python
import json
from pathlib import Path

from eggcup_leaderboard.providers.premier_league.normalizer import normalize_standings


def test_normalize_standings_maps_rows() -> None:
    fixture_path = Path("tests/fixtures/premier_league/standings_response.json")
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    rows = normalize_standings(payload)

    assert rows[0].team_name == "Liverpool"
    assert rows[0].points == 84
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_normalizer.py::test_normalize_standings_maps_rows -v`
Expected: FAIL with `ImportError` or missing `normalize_standings`

- [ ] **Step 3: 添加样例响应并实现最小规范化**

```json
{
  "tables": [
    {
      "entries": [
        {
          "team": {"club": {"name": "Liverpool", "shortName": "LIV"}},
          "position": 1,
          "overall": {
            "played": 38,
            "won": 25,
            "drawn": 9,
            "lost": 4,
            "points": 84,
            "goalDifference": 45
          }
        }
      ]
    }
  ]
}
```

```python
from eggcup_leaderboard.errors import NormalizeError
from eggcup_leaderboard.models import FixtureRow, Metadata, StandingRow


def normalize_standings(payload: dict) -> list[StandingRow]:
    try:
        entries = payload["tables"][0]["entries"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NormalizeError("standings payload missing tables[0].entries") from exc

    rows: list[StandingRow] = []
    for entry in entries:
        club = entry["team"]["club"]
        overall = entry["overall"]
        rows.append(
            StandingRow(
                team_id=club["shortName"].lower(),
                team_name=club["name"],
                rank=entry["position"],
                points=overall["points"],
                played=overall["played"],
                won=overall["won"],
                drawn=overall["drawn"],
                lost=overall["lost"],
                goal_difference=overall["goalDifference"],
            )
        )
    return rows
```

- [ ] **Step 4: 为 fixtures 和 metadata 增加测试与实现**

```python
import json
from pathlib import Path

from eggcup_leaderboard.providers.premier_league.normalizer import (
    normalize_fixtures,
    build_metadata,
)


def test_normalize_fixtures_maps_match_state() -> None:
    fixture_path = Path("tests/fixtures/premier_league/fixtures_response.json")
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    rows = normalize_fixtures(payload)

    assert rows[0].status == "FINISHED"
    assert rows[0].home_score == 2


def test_build_metadata_prefers_latest_round() -> None:
    metadata = build_metadata(
        season="2025-26",
        fetched_at="2026-05-29T12:00:00Z",
        latest_round="Matchweek 38",
    )

    assert metadata.latest_round == "Matchweek 38"
    assert metadata.source == "premierleague.com"
```

```json
{
  "matches": [
    {
      "id": "match-1",
      "status": "FINISHED",
      "kickoff": {"label": "2026-05-28T19:00:00Z"},
      "gameweek": {"compSeason": {"label": "2025/26"}, "gameweek": 38},
      "teams": [
        {"team": {"name": "Liverpool"}, "score": 2},
        {"team": {"name": "Arsenal"}, "score": 1}
      ]
    }
  ]
}
```

```python
def normalize_fixtures(payload: dict) -> list[FixtureRow]:
    try:
        matches = payload["matches"]
    except KeyError as exc:
        raise NormalizeError("fixtures payload missing matches") from exc

    rows: list[FixtureRow] = []
    for match in matches:
        teams = match["teams"]
        rows.append(
            FixtureRow(
                fixture_id=str(match["id"]),
                round_label=f"Matchweek {match['gameweek']['gameweek']}",
                kickoff_at=match["kickoff"]["label"],
                status=match["status"],
                home_team=teams[0]["team"]["name"],
                away_team=teams[1]["team"]["name"],
                home_score=teams[0].get("score"),
                away_score=teams[1].get("score"),
            )
        )
    return rows


def build_metadata(season: str, fetched_at: str, latest_round: str | None) -> Metadata:
    return Metadata(
        season=season,
        source="premierleague.com",
        fetched_at=fetched_at,
        latest_round=latest_round,
        match_progress=latest_round,
    )
```

- [ ] **Step 5: 跑测试并提交**

Run: `pytest tests/test_normalizer.py -v`
Expected: PASS

```bash
git add src/eggcup_leaderboard/providers/premier_league/normalizer.py tests/fixtures/premier_league/standings_response.json tests/fixtures/premier_league/fixtures_response.json tests/test_normalizer.py
git commit -m "feat: add premier league payload normalizers"
```

### Task 5: 串起 pipeline 并输出 artifacts

**Files:**
- Create: `src/eggcup_leaderboard/pipeline.py`
- Create: `src/eggcup_leaderboard/cli.py`
- Create: `tests/test_pipeline.py`
- Modify: `README.md`
- Create: `artifacts/raw/.gitkeep`
- Create: `artifacts/normalized/.gitkeep`

- [ ] **Step 1: 为 pipeline 写失败测试**

```python
import json
from pathlib import Path

from eggcup_leaderboard.pipeline import write_normalized_outputs
from eggcup_leaderboard.models import Metadata, StandingRow


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
        fixtures=[],
        metadata=metadata,
    )

    payload = json.loads((output_dir / "standings.json").read_text(encoding="utf-8"))
    assert payload[0]["team_name"] == "Liverpool"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL with missing `write_normalized_outputs`

- [ ] **Step 3: 实现落盘与编排逻辑**

```python
from pathlib import Path
import json

from eggcup_leaderboard.models import FixtureRow, Metadata, StandingRow


def write_normalized_outputs(
    output_dir: Path,
    standings: list[StandingRow],
    fixtures: list[FixtureRow],
    metadata: Metadata,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "standings.json").write_text(
        json.dumps([row.model_dump() for row in standings], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "fixtures.json").write_text(
        json.dumps([row.model_dump() for row in fixtures], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

```python
from datetime import UTC, datetime
from pathlib import Path

from eggcup_leaderboard.config import load_provider_config
from eggcup_leaderboard.pipeline import write_normalized_outputs
from eggcup_leaderboard.providers.premier_league.client import fetch_json
from eggcup_leaderboard.providers.premier_league.discovery import build_endpoint_urls
from eggcup_leaderboard.providers.premier_league.normalizer import (
    build_metadata,
    normalize_fixtures,
    normalize_standings,
)
from eggcup_leaderboard.providers.premier_league.snapshots import write_raw_snapshot


def main() -> int:
    root = Path.cwd()
    config = load_provider_config(root / "config" / "provider.yml")
    urls = build_endpoint_urls(config.base_url, config.endpoints)
    fetched_at = datetime.now(UTC).isoformat()

    raw_dir = root / "artifacts" / "raw" / config.season
    normalized_dir = root / "artifacts" / "normalized" / config.season

    standings_payload = fetch_json(urls["standings"], config.timeout_seconds)
    fixtures_payload = fetch_json(urls["fixtures"], config.timeout_seconds)

    write_raw_snapshot(raw_dir, "standings", standings_payload)
    write_raw_snapshot(raw_dir, "fixtures", fixtures_payload)

    standings = normalize_standings(standings_payload)
    fixtures = normalize_fixtures(fixtures_payload)
    latest_round = fixtures[-1].round_label if fixtures else None
    metadata = build_metadata(config.season, fetched_at, latest_round)

    write_normalized_outputs(normalized_dir, standings, fixtures, metadata)
    return 0
```

- [ ] **Step 4: 增加 CLI 入口、README 和最终验证**

```python
from eggcup_leaderboard.pipeline import main as run_pipeline


def main() -> int:
    return run_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
```

```markdown
## 第一里程碑运行方式

1. 安装依赖：`python -m pip install -e ".[dev]"`
2. 调整 `config/provider.yml` 中的入口路径
3. 执行：`eggcup-pipeline`
4. 检查 `artifacts/raw/<season>/` 与 `artifacts/normalized/<season>/`
```

Run: `pytest tests/test_pipeline.py tests/test_normalizer.py tests/test_discovery.py tests/test_provider_client.py tests/test_models.py tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/eggcup_leaderboard/pipeline.py src/eggcup_leaderboard/cli.py README.md artifacts/raw/.gitkeep artifacts/normalized/.gitkeep tests/test_pipeline.py
git commit -m "feat: wire data pipeline cli and artifact outputs"
```

### Task 6: 失败路径与回归保护

**Files:**
- Modify: `tests/test_provider_client.py`
- Modify: `tests/test_normalizer.py`
- Modify: `tests/test_pipeline.py`
- Modify: `src/eggcup_leaderboard/providers/premier_league/client.py`
- Modify: `src/eggcup_leaderboard/providers/premier_league/normalizer.py`

- [ ] **Step 1: 写失败路径测试**

```python
import pytest

from eggcup_leaderboard.errors import DiscoveryError, NormalizeError
from eggcup_leaderboard.providers.premier_league.client import fetch_json
from eggcup_leaderboard.providers.premier_league.normalizer import normalize_standings


def test_fetch_json_raises_discovery_error_on_404(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://www.premierleague.com/api/standings",
        status_code=404,
        json={"detail": "missing"},
    )

    with pytest.raises(DiscoveryError):
        fetch_json("https://www.premierleague.com/api/standings", timeout_seconds=5)


def test_normalize_standings_raises_on_missing_entries() -> None:
    with pytest.raises(NormalizeError):
        normalize_standings({"tables": []})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_provider_client.py tests/test_normalizer.py -v`
Expected: FAIL because current implementation lacks required assertions or messages

- [ ] **Step 3: 补全最小错误处理**

```python
def fetch_json(url: str, timeout_seconds: int) -> dict:
    try:
        response = httpx.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise DiscoveryError(f"failed to fetch {url}: {exc}") from exc
    except ValueError as exc:
        raise DiscoveryError(f"invalid json from {url}") from exc

    if not isinstance(payload, dict):
        raise DiscoveryError(f"unexpected payload type from {url}")
    return payload
```

```python
def normalize_standings(payload: dict) -> list[StandingRow]:
    try:
        entries = payload["tables"][0]["entries"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NormalizeError("standings payload missing tables[0].entries") from exc

    if not entries:
        raise NormalizeError("standings payload contains no entries")

    rows: list[StandingRow] = []
    for entry in entries:
        club = entry["team"]["club"]
        overall = entry["overall"]
        rows.append(
            StandingRow(
                team_id=club["shortName"].lower(),
                team_name=club["name"],
                rank=entry["position"],
                points=overall["points"],
                played=overall["played"],
                won=overall["won"],
                drawn=overall["drawn"],
                lost=overall["lost"],
                goal_difference=overall["goalDifference"],
            )
        )
    return rows
```

- [ ] **Step 4: 跑完整回归**

Run: `pytest -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/eggcup_leaderboard/providers/premier_league/client.py src/eggcup_leaderboard/providers/premier_league/normalizer.py tests/test_provider_client.py tests/test_normalizer.py tests/test_pipeline.py
git commit -m "test: add failure-path coverage for data pipeline"
```
