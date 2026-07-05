# 计划：CI 增强 + README 修复

## 1. 任务概要

- **CI 增强**：在现有的 `validate.yml` 中添加一个 `smoke-test` job，在 frontmatter 验证通过后，自动运行 `test_toolchain.sh` 进行端到端冒烟测试。
- **README 修复**：技能数量经核实为 **96**，与 README 中声明一致，无需修改。但需检查并修复其他潜在问题。
- **权限修复**：确保 `test_toolchain.sh` 可执行（`chmod +x`）。

## 2. 改动清单

### 2.1 CI 增强 —— `.github/workflows/validate.yml`

- 在现有 `validate` job 之后，新增一个 `smoke-test` job。
- 使用 `needs: validate` 保证顺序依赖。
- 运行环境：`ubuntu-latest`。
- 步骤：
  1. 检出代码（`actions/checkout@v4`）。
  2. 设置 Python（`actions/setup-python@v5`，Python 3.x）。
  3. 安装依赖：`pip install pyyaml`。
  4. 安装系统依赖：`sudo apt-get update && sudo apt-get install -y zip unzip`。
  5. 赋予脚本可执行权限：`chmod +x scripts/*.sh`。
  6. 运行冒烟测试：`./scripts/test_toolchain.sh coding/refactor`。

### 2.2 确保脚本可执行

- 在 Git 中跟踪 `scripts/test_toolchain.sh` 的可执行权限（`git add --chmod=+x`）。

### 2.3 README 修复

- 技能计数（96）和类别计数（59+26+5+3+3=96）经核实完全一致，无需修改。
- 检查有无过期链接、语句不通顺等其他问题——如果发现则修复。

## 3. 实施步骤

1. 编辑 `.github/workflows/validate.yml`，在末尾追加 `smoke-test` job。
2. 运行 `chmod +x scripts/test_toolchain.sh` 确保可执行。
3. 使用 `git ls-files` 检查是否需要 `git update-index --chmod=+x`。
4. 如果 README 中有明显问题，一并修复。
5. 本地运行 `./scripts/test_toolchain.sh` 验证通过。
6. 总结改动。

## 4. 验证方式

- 本地运行：`./scripts/test_toolchain.sh coding/refactor` 应全部通过。
- CI 中 `smoke-test` job 应能在 push/PR 时自动触发并通过。

## 5. 风险

- `test_toolchain.sh` 需要 `PyYAML` 和 `zip`/`unzip`，CI job 中已包含安装步骤，风险低。
- `test_toolchain.sh` 中有篡改测试步骤，CI 环境已有 Python 3 和 zip 支持，预期正常通过。
