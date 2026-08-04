# Changelog

## [3.5.1] - 2026-08-04

### Changed
- 数据访问切换为 `kk_common` 金融数据网关（`get_finance_data_gateway`），不再直接 `import tushare`，符合数据访问边界约束。
- 移除个股趋势预测（机器学习）能力：删除趋势预测相关脚本与依赖清单，收敛为十四维分析引擎。
- 修复 `from analysis.* import` 残留断链（analysis/ 目录已更名 analysis-engine/），改为注入 analysis-engine 路径后直接导入。

## [3.5.0] - 2026-07-03

### Added
- Initial standardized package structure.
