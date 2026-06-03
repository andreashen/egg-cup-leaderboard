# 茶叶蛋杯英超竞猜榜单 (Egg Cup Leaderboard)

这是一个用于自动计算“茶叶蛋杯”英超排名竞猜积分的系统。项目根据玩家的竞猜输入，结合英超实时赛果，自动计算积分榜并生成静态网页进行展示。

## 项目目标

- 自动拉取 `premierleague.com` 官方数据。
- 基于预设的竞猜规则（前四、黑马、黑驴），计算每位玩家的得分。
- 自动生成静态 HTML/JSON 文件，并部署到 GitHub Pages。
- 通过 GitHub Actions 实现定时（每 6 小时）和手动触发的自动化更新流。

## 文档指引

为了确保项目的开发与维护清晰透明，所有的设计思路、实施步骤和验收标准均已文档化：

- [竞猜规则 (game_rules.txt)](./docs/game_rules.txt) - 最核心的业务规则，包含计分公式和边界情况说明。
- [设计说明 (spec.md)](./docs/spec.md) - 项目的整体架构、数据流、数据模型和核心方案。
- [任务清单 (tasks.md)](./docs/tasks.md) - 开发实施的具体步骤和拆解任务。
- [验收清单 (checklist.md)](./docs/checklist.md) - 交付与验收的具体检查项。

## 快速开始

### 安装依赖

```bash
pip install httpx beautifulsoup4 pyyaml jinja2 click lxml
```

### 本地运行（完整流程）

```bash
# 抓取数据 → 计分 → 生成站点
PYTHONPATH=. python3 -m src.cli update --guesses data/guess.csv

# 仅使用已有快照重新计分（不重新抓取）
PYTHONPATH=. python3 -m src.cli score --guesses data/guess.csv
```

### 玩家竞猜 CSV 格式

```
UID,玩家类型,玩家昵称,英超第1,英超第2,英超第3,英超第4,黑马,黑驴
1,玩家,小明,切尔西,阿森纳,利物浦,曼城,曼联、伯恩茅斯,布伦特福德
```

- 多个黑马/黑驴用中文顿号（`、`）或英文逗号（`,`）分隔
- 球队名支持中文名、英文名、简称（见 `data/team_aliases.csv`）

### 运行测试

```bash
PYTHONPATH=. python3 -m pytest tests/ -v
```

## 目录结构

```
.
├── data/
│   ├── seasons/2025-26.yml       # 赛季配置
│   ├── baselines/2024-25_table.csv  # 上赛季基线积分榜
│   ├── team_aliases.csv          # 球队名称映射
│   └── guess.csv                 # 玩家竞猜（需自行创建）
├── src/
│   ├── models/                   # 数据模型
│   ├── providers/                # 官网数据抓取适配层
│   ├── scoring/                  # 计分引擎
│   ├── site/                     # 静态站点生成器
│   ├── utils/                    # 通用工具（映射、加载器）
│   └── cli.py                    # CLI 命令入口
├── config/
│   ├── provider.yml              # 数据源配置
│   └── site.yml                  # 站点元数据
├── tests/                        # 单元测试
├── docs/                         # 设计文档
├── artifacts/                    # 生成产物（快照、计分结果）- 不进入版本库
└── site/                         # GitHub Pages 发布目录 - 不进入版本库
```

## 开发与协作

本项目采用 Python 3.12 作为数据处理和计分引擎，生成的页面以无框架依赖的静态网页为主。
任何角色的开发者在接手或协作时，请首先阅读 `docs/` 目录下的文档，以对齐技术方案和计分逻辑。

## 下赛季复用

换赛季时需更新以下文件：
1. `data/seasons/<新赛季>.yml` - 新赛季队伍和升班马信息
2. `data/baselines/<上赛季>_table.csv` - 上赛季最终积分榜
3. `data/team_aliases.csv` - 如有新球队加入，补充别名
4. `config/provider.yml` 中的 `current_season_id` - 更新为新赛季 API ID

## 故障排查

- **抓取失败**：检查 `artifacts/standings_raw.json`，确认 API 响应格式是否变化
- **球队名映射失败**：向 `data/team_aliases.csv` 补充新别名
- **计分异常**：检查 `artifacts/scoring_results.json`，对照 `docs/game_rules.txt` 逐项核对
