# KSkills — 跨平台技能包仓库

KSkills 是一套面向 Coding Agent / OClaw 平台的**技能包（Skill Pack）集合**。每个技能是一个独立目录，核心是 `SKILL.md` 文件（YAML frontmatter + Markdown 指南），按类别归档，开箱即用。

本仓库共收录 **95 个技能**，覆盖软件工程、金融量化、内容创作、深度研究四大领域。

---

## 目录结构

```
KSkills/
├── coding/     # 软件工程技能（59）
├── stock/      # 金融量化技能（28）
├── media/      # 内容创作技能（5）
├── research/   # 深度研究技能（3）
├── common/     # 跨领域公共技能（2）
└── scripts/    # 维护工具（frontmatter 校验器 + 打包/安装/卸载）
```

每个技能目录约定：

```
<category>/<skill-name>/
└── SKILL.md      # 唯一入口：frontmatter（元数据）+ 正文（指南）
```

---

## 技能总览

### 🖥 coding — 软件工程（59）

覆盖软件交付全生命周期：需求 → 设计 → 编码 → 测试 → 审查 → 发布 → 运维。

| 类别 | 技能 |
|------|------|
| **规划与需求** | `requirements-analysis` `product-spec` `technical-design` `architecture` `task-decomposition` `planning` `project-delivery-workflow` `project-scaffolding` |
| **编码实现** | `implement` `refactor` `migration` `vertical-slice-development` `api-design` `database` `state-management` `typescript` `react-nextjs` `fastapi-backend` `frontend-engineering` |
| **质量与测试** | `test-driven-development` `test-writer` `qa-test-plan` `code-review` `pr-review-advanced` `acceptance-criteria` `verification-before-completion` `playwright-verification` `webapp-testing` `web-accessibility` |
| **调试与运维** | `debug` `systematic-debugging` `error-handling` `observability` `performance` `operations-runbook` `deployment` `ci-cd` `release-engineering` `rollback-recovery` |
| **工程治理** | `security-hardening` `security-review` `build-system` `dependency-upgrade` `diff-analysis` `codebase-analysis` `environment-setup` `scratch-workspace` `using-git-worktrees` `workflow-automation` `ui-polish` `patch-authoring` |
| **文档与协作** | `docs` `handoff-docs` `context-management` `agent-memory-isolation` `subagent-orchestration` `skill-authoring` `using-superpowers` `qiongqi-roi` |

### 📈 stock — 金融量化（28）

A股 / 港股 / 美股 / 期货 / 期权的量化分析与数据查询技能。

| 类别 | 技能 |
|------|------|
| **数据源（唯一官方入口）** | `tushare-data`（Tushare 官方适配包；分析技能禁止直接 import tushare，须通过 `kk-common` 的 `FinanceDataGateway` 或 `TushareClient` 访问） |
| **数据查询** | `kk-common`（金融数据网关 + iWencai/Tushare 统一客户端）`kk-zhishu-query` `kk-business-query` `kk-event-query` `kk-macro-query` `kk-announcement-search` `kk-news-search` `kk-report-search` `kk-hithink-futures` |
| **个股分析** | `kk-stock-analysis`（十五维一体）`kk-financial-statement`（三表深度解读）`kk-valuation-model`（DCF/DDM/SOTP）`kk-cb-analysis`（可转债）`kk-etf-analysis` |
| **量化研究** | `kk-factor-research`（因子研究）`kk-strategy-research`（策略回测）`backtrader-strategies`（策略适配器库）`kk-selection-strategies` `a-stock-screener`（对话式选股） |
| **衍生品** | `kk-futures-analysis`（股指期货）`kk-options-payoff`（盈亏分析）`kk-options-volatility`（波动率） |
| **市场宏观** | `kk-industry-analysis`（行业六维一体）`kk-market-linkage-engine`（市场联动）`kk-earnings-forecast`（盈利预测）`kk-earnings-revision`（预期修正）`kk-mcf` |

> **变更说明**：原 `kk-chan-theory`（缠论）已内嵌为 `kk-stock-analysis/chan_theory_v2/`，不再作为独立技能分发；原 `kk-backtrader-strategies` 重命名为 `backtrader-strategies`（Python 包名对齐）。

### 🎨 media — 内容创作（5）

`baoyu-comic`（知识漫画）`image-generation`（图像）`music-generation`（音乐）`podcast-generation`（播客）`video-generation`（视频）

### 🔬 research — 深度研究（3）

`deep-research`（深度网络研究）`academic-paper-review`（学术论文审阅）`consulting-analysis`（咨询报告）

### 🧰 common — 跨领域公共（2）

`analysis-report`（结构化分析报告，强制 Markdown + 暗色/亮色双主题 HTML 看板）`chart-visualization`（26 种图表）

---

## SKILL.md 规范

每个 `SKILL.md` 由 **YAML frontmatter**（`---` 包裹的元数据块）和 **Markdown 正文**（使用指南）两部分组成。

### Frontmatter 字段

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `name` | ✅ | string | 技能唯一标识 |
| `description` | ✅ | string | 技能描述 / 触发说明 |
| `version` | ✅ rich | string | 语义化版本，如 `1.0.0` |
| `author` | ✅ rich | string | 作者 |
| `license` | ✅ rich | string | 许可证，如 `MIT` / `Apache-2.0` |
| `capabilities` | ✅ rich | list | 能力清单，每项含 `id` + `description` |
| `permissions` | ✅ rich | object | 运行权限：`network` / `filesystem` / `shell` / `env` |
| `metadata` | ✅ rich | object | 扩展元数据，含 `openclaw` 子对象 |
| `tags` | ✅ rich | list | 标签（非空列表） |
| `requires` | ⬜ | object | 运行依赖：`bins` / `packages` / `env` |
| `inputs` | ⬜ | list | 输入参数定义 |
| `category` | ⬜ | string | 分类 |

> **Profile 说明**：`stock` 和 `common` 类别采用 **rich** profile（需全套字段）；`coding` / `media` / `research` 采用 **minimal** profile（仅需 `name` + `description`）。

### 示例（rich profile）

```yaml
---
name: kk-factor-research
description: 量化因子研究公共技能包——整合因子方法论、IC/IR分析、分层回测...
version: 1.0.0
author: kk-quant
license: Apache-2.0

capabilities:
  - id: factor-analysis
    description: "IC/IR 统计分析 + 分层回测，检验单因子有效性"

permissions:
  network: false
  filesystem: true
  shell: true

requires:
  bins: ["python3"]
  packages: ["pandas", "numpy", "scipy"]

metadata:
  openclaw:
    emoji: "🔬"
    version: "1.0.0"
    author: "kk-quant"
    category: "finance"
    tags:
      - finance
      - factor-research

tags:
  - finance
  - factor-research
---

# kk-factor-research

正文：使用指南、工作流程、示例...
```

---

## 校验

仓库内置 frontmatter 校验器，确保所有 `SKILL.md` 符合字段规范：

```bash
# 校验全部
python3 scripts/validate_skills.py .

# 校验指定目录
python3 scripts/validate_skills.py stock
```

输出按严重程度分级：`ERROR`（缺失必填字段 / YAML 解析失败）、`WARN`（名称不匹配等）、`INFO`（建议项缺失）。退出码非零表示存在 ERROR。

### Pre-commit Hook（推荐）

提交前自动校验，防止无效 frontmatter 入库：

```bash
# 安装（一次性）
python3 scripts/install-hooks.py        # 跨平台

# 或手动设置
git config core.hooksPath .githooks

# 临时跳过校验
SKIP_VALIDATION=1 git commit
```

### CI Pipeline

仓库已配置 GitHub Actions 自动校验（`.github/workflows/validate.yml`），每次 push / PR 自动运行：

```bash
# 本地模拟 CI
pip install pyyaml
python3 scripts/validate_skills.py .
```

---

## 打包与分发

每个技能可独立打包成 `.skill` 压缩包（zip 格式），便于在其他平台（Claude Code / OClaw / Qoder 等）安装使用。

### 打包

```bash
# 打包单个技能（最常用）
python3 scripts/build_skill.py stock/kk-business-query

# 指定输出目录（默认 dist/）
python3 scripts/build_skill.py coding/test-driven-development -o ./releases

# 批量打包所有技能
python3 scripts/build_skill.py --all

# 跳过校验快速打包（调试用，不推荐）
python3 scripts/build_skill.py stock/kk-business-query --no-validate
```

输出：`dist/<name>-<version>.skill`，内含技能全部文件 + 自动生成的 `SKILL-MANIFEST.json` 清单（含每个文件的 sha256 校验和、依赖声明）。

**自动排除**：`__pycache__/`、`.pytest_cache/`、`__MACOSX/`、`node_modules/`、`.DS_Store`、`*.pyc` 等构建产物与系统缓存。

### 安装

安装器不假设目标目录 —— 由调用平台通过参数指定：

```bash
# 安装到指定目录（平台负责选择目标位置）
./scripts/install_skill.sh dist/kk-business-query-1.0.0.skill ~/.agents/skills/

# 仅查看包内容
./scripts/install_skill.sh dist/kk-business-query-1.0.0.skill --list

# 校验包完整性（zip + sha256）
./scripts/install_skill.sh dist/kk-business-query-1.0.0.skill --verify

# 强制覆盖已存在的安装
./scripts/install_skill.sh dist/kk-business-query-1.0.0.skill ~/.agents/skills/ --force

# 非交互模式（自动执行 install.sh，适用于 CI）
KSKILLS_AUTO_INSTALL=1 ./scripts/install_skill.sh dist/foo.skill ~/.agents/skills/
```

安装流程：① 压缩包完整性校验 → ② sha256 文件校验 → ③ 解压到目标目录 → ④ 环境变量检查（按 `permissions.env` 声明）→ ⑤ 询问是否执行 `install.sh`（安装 Python 依赖等）。

### SKILL-MANIFEST.json

每个 `.skill` 包内自动生成的清单文件：

```json
{
  "name": "kk-business-query",
  "version": "1.0.0",
  "package_type": "python",       // knowledge-only | python | node
  "entry": "scripts/cli.py",
  "requires": {
    "bins": ["python3"],
    "packages": ["pandas"],
    "env": ["IWENCAI_API_KEY"]
  },
  "files": [
    {"path": "SKILL.md", "sha256": "...", "size": 1234}
  ]
}
```

### 按技能类型区别

| 类型 | `.skill` 包含 | 安装复杂度 |
|------|---------------|-----------|
| **knowledge-only**（coding/ 大多数） | SKILL.md + CHANGELOG.md | 解压即用 |
| **python**（stock/ 多数） | 全量 + scripts/ + requirements.txt | 解压 + 可选 `pip install` |
| **node**（chart-visualization） | 全量 + package.json | 解压 + 可选 `npm install` |

---

## 许可证

各技能许可证见其 frontmatter 的 `license` 字段。
