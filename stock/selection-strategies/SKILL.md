---
name: selection-strategies
description: A股多策略选股运行框架，提供10种经典选股策略的CLI运行脚本，涵盖成长股、价值投资、高股息、动量突破、技术突破、超跌反弹、涨停龙头、主力资金追踪、缠论背驰选股与多因子横截面。每种策略独立运行、可配置参数，支持市值/股票池过滤与结果导出。
version: 1.0.0
author: kk-quant
license: MIT
category: finance


package:
  type: python
requires:
  packages: ["numpy", "pandas"]
required-secrets:
  - TUSHARE_TOKEN

capabilities:
  - id: growth-stock-selection
    description: "成长股策略：EPS/营收增速双驱动，PEG 0.2~1.5，分级筛选成长性40%+盈利能力35%+创新投入15%+财务安全10%"
  - id: value-investment
    description: "价值投资策略：低PE+低PB+高ROE+高股息率，分级筛选估值30%+质量30%+股息25%+安全15%"
  - id: high-dividend
    description: "高股息策略：股息率≥4%+连续分红+低波动，分级筛选股息35%+稳定性30%+质量20%+估值15%"
  - id: momentum-breakthrough
    description: "动量突破策略：20/60日动量+量比放大+均线排列多头，分级筛选动量35%+趋势30%+资金20%+量能15%"
  - id: technical-breakthrough
    description: "技术突破策略：突破年线/箱体+缩量回踩确认+MACD金叉，分级筛选趋势35%+突破30%+量能20%+动能15%"
  - id: oversold-rebound
    description: "超跌反弹策略：RSI<30+乖离率<-15%+底部放量，分级筛选超跌40%+反转30%+资金20%+量能10%"
  - id: limit-up-leader
    description: "涨停龙头策略：涨停+板块共振+龙头特征，分级筛选强度40%+辨识度30%+板块效应20%+量价10%"
  - id: fund-flow-tracking
    description: "主力资金追踪策略：北向/主力净流入+机构调研，分级筛选资金40%+机构25%+趋势20%+估值15%"
  - id: chan-theory-selection
    description: "缠论背驰选股：底背驰/顶背驰+MACD背驰信号+三类买卖点，分级筛选背驰40%+中枢30%+量价20%+动能10%"
  - id: multi-factor-selection
    description: "多因子横截面选股：动量/反转/波动率/SIZE/估值/成长/质量七大因子Z-score标准化+等权/自定义加权+TopN组合构建"

permissions:
  network: false
  filesystem: true
  shell: true

metadata:
  openclaw:
    emoji: "🎯"
    version: "1.0.0"
    author: "kk-quant"
    category: "finance"
    tags:
      - finance
      - stock-selection
      - A-share
      - strategy
      - quantitative

tags:
  - finance
  - stock-selection
  - A-share
  - strategy
  - quantitative
---

# selection-strategies

A股多策略选股运行框架，提供 10 种经典选股策略的独立 CLI 脚本，每种策略支持参数配置、市值/股票池过滤与 JSON/CSV 结果导出。

## 策略脚本清单（位于技能包根目录）

| 脚本 | 策略 | 依赖 |
|------|------|------|
| `run_growth_stock.py` | 成长股（EPS/营收双驱动 + PEG） | backtrader_strategies |
| `run_value_investment.py` | 价值投资（低PE/PB + 高ROE） | backtrader_strategies |
| `run_high_dividend.py` | 高股息（股息率≥4% + 连续分红） | backtrader_strategies |
| `run_momentum_breakthrough.py` | 动量突破（20/60日动量 + 量比） | backtrader_strategies |
| `run_technical_breakthrough.py` | 技术突破（年线/箱体 + MACD金叉） | backtrader_strategies |
| `run_oversold_rebound.py` | 超跌反弹（RSI<30 + 乖离率） | backtrader_strategies |
| `run_limit_up_leader.py` | 涨停龙头（连板 + 板块共振） | backtrader_strategies |
| `run_fund_flow_tracking.py` | 主力资金追踪（北向/净流入） | backtrader_strategies |
| `run_multi_factor.py` | 多因子横截面（7因子 Z-score + TopN） | numpy / pandas |
| `run_chan_stock_selector.py` | 缠论背驰选股（wrapper） | **stock-analysis + stock/common** |

## 依赖技能包

- **`stock/backtrader_strategies`**：8 个策略脚本的适配器库（`from backtrader_strategies.strategy_adapters...`），需将该包加入 `PYTHONPATH` 或安装。
- **`stock/stock-analysis`**：缠论选股引擎（`scripts/run_chan_stock_selector.py` 完整实现 + `chan_theory_v2/` 缠论模块）。本技能中的 `run_chan_stock_selector.py` 为薄封装，通过相对路径调用该引擎，请勿单独分发使用。
- **`stock/common`**：`kk_common` 金融数据网关（缠论引擎数据入口）。
- 环境变量 `TUSHARE_TOKEN`：全部策略的数据访问凭证。

## 使用示例

```bash
# 价值投资策略
python run_value_investment.py --json

# 多因子横截面（Top20 等权组合）
python run_multi_factor.py --top-n 20 --json

# 缠论背驰选股（需先安装 stock-analysis 与 stock/common）
python run_chan_stock_selector.py --pool hs300 --signal buy --json
```

> 所有策略脚本均在技能包根目录运行：`cd stock/selection-strategies && python run_xxx.py`
