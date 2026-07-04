---
name: analysis-report
description: 统一分析报告格式，所有分析类任务默认生成结构化报告；支持通过 chart-visualization 技能在报告中嵌入可视化图表
version: 1.0.0
author: kk-quant
license: MIT
category: report


package:
  type: knowledge-only
capabilities:
  - id: report-generation
    description: "结构化分析报告生成：执行摘要+数据概览+核心分析+风险提示+参考资料"
  - id: chart-embedding
    description: "图表嵌入：通过 chart-visualization 技能在报告中嵌入26种可视化图表"

permissions:
  filesystem: true
  shell: true

requires:
  bins: ["python3"]

inputs:
  - name: analysis_type
    type: string
    required: false
    description: "分析类型，决定报告模板选择"

metadata:
  openclaw:
    emoji: "📋"
    version: "1.0.0"
    author: "kk-quant"
    category: "report"
    tags:
      - report
      - analysis
      - visualization
      - chart
    requires:
      bins: ["python3"]

tags:
  - report
  - analysis
  - visualization
  - chart
---

# 分析报告格式规范

## 核心原则

**当用户请求任何分析任务时，必须自动生成结构完整的分析报告，无需额外提示。**

### 例外场景（必须排除）

当系统提示词、用户要求或当前任务上下文中出现以下任一信号时，**禁止使用本技能**，必须让位给 HTML 数据看板流程：
- 出现 **「专题页模式」**
- 明确要求生成 **HTML 数据看板 / 数据看板 / dashboard**
- 明确要求调用 `generate_dashboard`
- 明确要求最终产物为 `.html` 文件

以上场景下，**绝对禁止**生成、保存或展示 `.md` 分析报告。

## 报告输出方式

由于用户需要下载结构化分析报告，你**必须**使用以下方式将最终的报告写入文件：

1. **组合报告内容**：将分析得到的所有数据、指标、结论组合成完整的 Markdown 文本。
2. **保存报告文件**：使用 `write_file` 工具将该 Markdown 内容保存为 `.md` 文件。**必须**保存到 `/mnt/user-data/outputs/` 目录下（如：`/mnt/user-data/outputs/{分析对象}_分析报告.md`）。
3. **展示给用户**：在聊天回复中，使用 `present_files` 工具将刚才保存的报告文件展示给用户（参数 `filepaths` 为刚才的绝对路径）。

## 报告结构

所有分析结果必须包含以下五个部分，按顺序完整呈现：

### 1. 执行摘要
- 一句话总结核心结论
- 明确给出操作建议（买入/卖出/持有/观望）
- 风险等级评估（高/中/低）

### 2. 数据概览
- 使用表格展示关键指标
- 包含当前值、环比变化、同比变化
- 数据来源标注清晰

### 3. 核心分析
- 详细解读数据背后的含义
- 结合市场环境和行业趋势
- 指出异常点和关键信号

### 4. 风险提示
- 列出可能影响结论的风险因素
- 数据局限性说明
- 历史表现不代表未来

### 5. 参考资料
- 引用数据来源
- 相关新闻或公告
- 使用 `[citation:标题](URL)` 格式

## 报告模板

```markdown
# {分析对象} 分析报告
**生成时间**: {YYYY-MM-DD HH:mm} | **分析师**: AI

---

## 1. 执行摘要

| 指标 | 数值 | 信号 |
|------|------|------|
| 总体评级 | ⭐⭐⭐☆☆ | 中性 |

**核心结论**: {一句话总结}

**操作建议**: {买入/卖出/持有/观望}

---

## 2. 数据概览

| 指标 | 当前值 | 环比 | 同比 |
|------|--------|------|------|
| {指标1} | {值} | {变化} | {变化} |
| {指标2} | {值} | {变化} | {变化} |

---

## 3. 核心分析

{详细分析内容}

---

## 4. 风险提示

⚠️ **风险因素**:
- {风险1}
- {风险2}

---

## 5. 参考资料

- [数据来源名称](URL)
```

## 参考资料

- [数据来源名称](URL)

完成报告后自检：
- [ ] 是否包含执行摘要（一句话结论+操作建议）？
- [ ] 是否包含数据表格（指标+数值+变化）？
- [ ] 是否包含核心分析（不少于3个要点的详细解读）？
- [ ] 是否包含风险提示（至少2项）？
- [ ] 是否标注了数据来源？

## 图表可视化（chart-visualization 技能）

当报告中需要可视化图表时，**必须**使用 `chart-visualization` 公共技能生成：

### 生成流程
1. **选择图表类型**：根据数据特征选择最合适的图表（参见 chart-visualization/references/ 目录下 26 种图表规格）
2. **构造参数**：按对应图表类型的参考文档提取 `args`
3. **调用生成脚本**：
   ```bash
   node ./skills/chart-visualization/scripts/generate.js '{"tool":"generate_line_chart","args":{"data":[...],"title":"..."}}'
   ```
4. **嵌入报告**：脚本返回图片 URL，使用 Markdown 图片语法嵌入报告：
   ```markdown
   ![图表说明](返回的图片URL)
   ```

### 常用图表类型速查

| 场景 | 图表工具名 | 说明 |
|------|-----------|------|
| 趋势/走势 | `generate_line_chart` | 折线图，适合时间序列 |
| 对比/排名 | `generate_bar_chart` / `generate_column_chart` | 条形图/柱状图 |
| 占比/结构 | `generate_pie_chart` / `generate_treemap_chart` | 饼图/矩形树图 |
| 多维评估 | `generate_radar_chart` | 雷达图，适合五维评分等 |
| 分布/统计 | `generate_boxplot_chart` / `generate_histogram_chart` | 箱线图/直方图 |
| 相关性 | `generate_scatter_chart` | 散点图 |
| 流程/转化 | `generate_funnel_chart` / `generate_flow_diagram` | 漏斗图/流程图 |
| 表格数据 | `generate_spreadsheet` | 表格/交叉表 |

### 何时生成图表
- **必须生成**：当数据包含时间序列趋势、多维对比、占比结构时
- **推荐生成**：当纯文字+表格难以直观表达数据关系时
- **无需生成**：纯文字分析、简单指标列表

### ⚠️ 禁止事项
- **禁止**使用 `:::chart` 块内联图表语法
- **禁止**使用 ` ```mermaid ` 代码块生成图表
- **禁止**使用 `display_chart` 工具
- 图表生成**只能**通过 `chart-visualization/scripts/generate.js`

### 中文字体配置
`generate.js` 和 `/chart/generate` API 路由已内置中文字体配置（`fontFamily`），确保图表中的中文标题、轴标签、图例正确渲染。如果私有化部署的 GPT-Vis-SSR 服务仍然出现中文乱码（方块□□□），需在服务器系统上安装中文字体（如 `Noto Sans CJK`、`ChillZhuo`），或通过 `VIS_REQUEST_SERVER` 环境变量指向已安装中文字体的渲染服务。
