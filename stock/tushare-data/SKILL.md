---
name: tushare-data
description: Tushare 官方数据适配技能——A 股/指数/ETF/基金/期货/期权/财务/估值/资金流/宏观全量数据获取的唯一官方入口，分析类技能必须通过本技能或 kk-common.finance_data_gateway 间接调用，禁止直接 import tushare
version: 1.1.16
author: tushare.pro
license: Official Tushare Skill terms
category: finance

package:
  type: python
  entry: scripts/stock_data_demo.py
capabilities:
  - id: market-data
    description: "行情数据：daily/weekly/monthly/pro_bar/stk_mins，A 股/指数/ETF/基金/期货/期权日线与分钟行情"
  - id: fundamentals
    description: "基本面数据：stock_basic/fina_indicator/income/balancesheet/cashflow/forecast/express/dividend"
  - id: valuation
    description: "估值数据：daily_basic（PE/PB/股息率/总市值）"
  - id: capital-flow
    description: "资金流数据：moneyflow/moneyflow_hsgt/hsgt_top10/top_list/top_inst/margin/margin_detail"
  - id: macro-data
    description: "宏观数据：cn_cpi/cn_ppi/cn_pmi/cn_gdp/cn_m/shibor/shibor_lpr/us_tycr"
  - id: data-export
    description: "数据导出：CSV/parquet，按标的+日期分段拉取、去重、排序、命名规范"

permissions:
  network: true
  filesystem: true
  shell: true
  env:
    - TUSHARE_TOKEN

requires:
  bins: ["python3"]
  packages: ["tushare", "pandas"]
  env: ["TUSHARE_TOKEN"]

metadata:
  openclaw:
    emoji: "📊"
    version: "1.1.16"
    author: "tushare.pro"
    category: "integration"
    tags:
      - finance
      - tushare
      - data-source
      - integration
    requires:
      bins: ["python3"]
      packages: ["tushare", "pandas"]
      env: ["TUSHARE_TOKEN"]
      network: true
    install:
      - id: pip-deps
        kind: pip
        package: "tushare pandas"
        python: python3
        label: "Install Tushare Pro SDK"

tags:
  - finance
  - tushare
  - data-source
  - integration
---

# Tushare 官方数据

本技能是 Tushare 官方 `tushare-data` Skill 在本仓库的内置适配包，是 **Tushare Pro 数据获取的唯一官方入口**。

## 数据访问边界（强制）

本仓库所有分析类技能获取 Tushare 数据时，**必须遵循以下边界，禁止绕过**：

1. **唯一允许直接 `import tushare` 的位置**：
   - 本技能 `scripts/`（官方示例）
   - `kk-common/src/kk_common/tushare_client.py`（兼容客户端实现）
2. **其余所有分析脚本**（`kk-stock-analysis`、`kk-futures-analysis`、`kk-etf-analysis`、`backtrader_strategies`、`kk-selection-strategies` 等）**禁止直接 `import tushare` 或调用 `ts.pro_api()`**，必须通过以下任一方式访问：
   - `from kk_common import get_finance_data_gateway; gw = get_finance_data_gateway(); df = gw.daily(ts_code='600519.SH')`
   - `from kk_common import get_tushare_client; client = get_tushare_client(); df = client.daily(ts_code='600519.SH')`
3. `kk-common.finance_data_gateway` 是分析技能的**首选入口**：方法名与 Tushare 官方接口一致，实现可替换，便于单元测试注入 mock 与后续切换运行时。
4. 缺少 token / 接口权限 / 积分时，返回结构化空 DataFrame，**禁止编造数据**。
5. 完整分析报告统一交由 `common/analysis-report` 渲染，不在本技能内生成。

## 使用边界

- 数据获取、接口选择、字段确认、日期规范化、单位说明和数据质量检查遵循 `UPSTREAM_SKILL.md`。
- 运行前必须确认 Python、`tushare` 包与 `TUSHARE_TOKEN` 凭证可用。
- 接口字段以 `references/数据接口.md` 与官方在线文档为唯一依据，不凭记忆硬写字段名。

## 自然语言触发场景

- 行情/趋势：看下 XX 最近怎么样、今年涨了多少、最近有没有放量
- 财务/估值：看下 XX 财报、ROE/毛利率如何、现在估值算高吗
- 对比/筛选：XX 和 YY 谁更强、帮我筛高 ROE 低负债、排个前十
- 板块/主题：最近哪个板块最强、半导体最近怎么样、某概念有哪些成分股
- 资金流/情绪：北向最近买什么、主力资金流入最多的是谁、龙虎榜看点
- 公告/新闻/研报：最近有什么公告、有什么催化、政策面发生什么
- 宏观/跨市场：CPI/PMI/社融/M2、利率曲线、港股/美股/美债
- 数据导出：拉一份 CSV、做回测数据表、导出 parquet

## 上游文件

- 官方原文：`UPSTREAM_SKILL.md`（上游版本 `1.1.16`）
- 官方接口参考：`references/数据接口.md`
- 官方示例：`scripts/stock_data_demo.py`、`scripts/fund_data_demo.py`
- 上游仓库：<https://github.com/waditu-tushare/skills>
- 官方文档：<https://tushare.pro/document/1?doc_id=473>
- 适配记录：`SOURCE.md`

详细的工作流模板、意图分类、实体解析、输入规范化、数据质量与错误处理规则，见 `UPSTREAM_SKILL.md`。
