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

## 开发与协作

本项目目前采用 Python 作为数据处理和计分引擎，生成的页面以无框架依赖的静态网页为主。
任何角色的开发者在接手或协作时，请首先阅读上述 `docs/` 目录下的文档，以对齐技术方案和计分逻辑。

## 第一里程碑运行方式

1. 安装依赖：`python -m pip install -e ".[dev]"`
2. 检查或调整 `config/provider.yml` 中的积分榜抓取入口配置。
3. 执行数据链路：`eggcup-pipeline`
4. 查看输出目录：`artifacts/raw/<season>/standings.json`、`artifacts/normalized/<season>/standings.json` 和 `artifacts/normalized/<season>/metadata.json`

## 计分引擎下一步

- 输入：竞猜 CSV、球队别名表、上赛季基线积分榜、当前 `standings.json`
- 输出：玩家总分、排名、前四明细、黑马明细、黑驴明细

## 目录结构概览

- `data/`: 保存玩家竞猜 CSV、赛季配置、球队基线数据等静态输入。
- `docs/`: 存放所有相关文档。
- `src/`: 核心逻辑代码（爬虫、计分、模型、页面生成）。
- `artifacts/`: 运行过程中生成的临时快照和计算结果。
- `site/`: 最终发布到 GitHub Pages 的静态站点文件。
- `.github/workflows/`: CI/CD 自动化工作流配置。
