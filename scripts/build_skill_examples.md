# .skill 打包与分发 — 使用示例

本文件通过具体场景演示如何使用 `build_skill.py`（打包器）和 `install_skill.sh`（安装器）。

---

## 场景 1：打包一个纯知识型技能（最简单）

适用于 `coding/`、`media/`、`research/` 下的纯指南类技能，无代码、无依赖。

```bash
# 打包
python3 scripts/build_skill.py coding/test-driven-development
# → dist/test-driven-development-0.0.0.skill (1.5 KB)

# 查看包内容
./scripts/install_skill.sh dist/test-driven-development-0.0.0.skill --list

# 安装到 Claude Code 的技能目录
./scripts/install_skill.sh dist/test-driven-development-0.0.0.skill ~/.agents/skills/
```

知识型技能无需运行时依赖，安装后 Claude Code 重启即可自动识别。

---

## 场景 2：打包一个 Python 技能（有代码 + API 依赖）

以 `stock/business-query` 为例（含 `scripts/cli.py`，依赖 `IWENCAI_API_KEY`）。

```bash
# 1. 打包
python3 scripts/build_skill.py stock/business-query
# → dist/business-query-1.0.0.skill

# 2. 校验完整性（推荐）
./scripts/install_skill.sh dist/business-query-1.0.0.skill --verify

# 3. 安装（交互模式，会询问是否执行 install.sh）
./scripts/install_skill.sh dist/business-query-1.0.0.skill ~/.agents/skills/
```

安装器输出示例：

```
🔍 环境变量检查
⚠  未设置：IWENCAI_API_KEY
  请设置以下变量后使用：
    export IWENCAI_API_KEY=<your-key>

🔧 安装脚本
  发现 install.sh，是否执行？（将安装运行时依赖，Y/n）: Y
✅ 安装成功
```

---

## 场景 3：打包带 setup.py 的复杂技能

以 `stock/announcement-search` 为例（含 `setup.py`、`__pycache__`、`.pytest_cache`）。

```bash
python3 scripts/build_skill.py stock/announcement-search
# → 自动排除 12 个污染文件（__pycache__、.pytest_cache、.DS_Store）
# → dist/announcement-search-1.0.0.skill (28.1 KB)
```

打包日志会显示：`16 文件, 排除 12`。

---

## 场景 4：批量打包所有技能

发布新版本时，一次性打包全部 96 个技能：

```bash
python3 scripts/build_skill.py --all
# → dist/ 目录下生成 96 个 .skill 文件
# → 总大小约 1.1 MB
```

---

## 场景 4b：打包某个类别目录下的所有技能

只需发布某个类别（如仅股票类、仅编码类）时，直接传入类别目录名，
脚本会自动识别并批量打包该目录下所有技能：

```bash
# 打包 stock/ 下全部 36 个技能
python3 scripts/build_skill.py stock
# → dist/business-query-1.0.0.skill
# → dist/factor-research-1.0.0.skill
# → ...

# 打包 coding/ 下全部技能，输出到指定目录
python3 scripts/build_skill.py coding -o ./releases

# 同时打包多个类别（在一条命令里）
python3 scripts/build_skill.py media research
# → 会先处理 media/ ，再处理 research/，末尾给出汇总
```

**智能识别规则**（无需新参数）：

| 传入路径                            | 脚本行为                         |
|------------------------------------|---------------------------------|
| `stock/business-query`（含 SKILL.md） | 打包单个技能（向后兼容）         |
| `stock`（不含 SKILL.md，但子目录有）   | 批量打包该类别下所有技能          |
| `stock coding/refactor`（混传）       | 先批量打包 stock/，再打包单个 refactor |
| 不含 SKILL.md 且无子技能的目录         | 报错退出                        |

---

## 场景 5：CI/CD 集成（非交互模式）

在 GitHub Actions 等 CI 环境中，用 `KSKILLS_AUTO_INSTALL=1` 跳过所有交互：

```bash
# 打包（CI 中可跳过校验以加速，或保留校验确保质量）
python3 scripts/build_skill.py stock/business-query --no-validate

# 安装（自动执行 install.sh，不询问）
KSKILLS_AUTO_INSTALL=1 ./scripts/install_skill.sh \
  dist/business-query-1.0.0.skill \
  ~/.agents/skills/
```

---

## 场景 6：升级已安装的技能

```bash
# 1. 用 --force 覆盖旧版本
./scripts/install_skill.sh dist/business-query-1.1.0.skill ~/.agents/skills/ --force

# 或先卸载再安装
rm -rf ~/.agents/skills/business-query
./scripts/install_skill.sh dist/business-query-1.1.0.skill ~/.agents/skills/
```

---

## 命令选型速查

| 需求                         | 推荐命令                                                |
|-----------------------------|--------------------------------------------------------|
| 打包一个技能                  | `build_skill.py stock/business-query`                 |
| 打包某类别下所有技能           | `build_skill.py stock`                                   |
| 同时打包多个类别/技能          | `build_skill.py media research coding/refactor`          |
| 打包整个仓库                  | `build_skill.py --all`                                   |
| 跳过校验（调试用）             | 追加 `--no-validate`                                      |
| 不生成清单文件                | 追加 `--no-manifest`                                      |

---

## SKILL-MANIFEST.json 字段说明

每个 `.skill` 包内都会自动生成此清单，用于校验和元数据查询：

| 字段 | 说明 |
|------|------|
| `name` | 技能名（与 frontmatter 一致） |
| `version` | 版本号 |
| `package_type` | `knowledge-only` / `python` / `node` |
| `entry` | 主入口文件（如 `scripts/cli.py`） |
| `requires.bins` | 需要的可执行文件（如 `python3`） |
| `requires.packages` | Python 依赖包列表 |
| `requires.env` | 必需的环境变量（如 `IWENCAI_API_KEY`） |
| `files[].sha256` | 每个文件的 sha256 校验和（用于完整性验证） |
| `built_at` | 打包时间（UTC ISO 格式） |

---

## 跨平台安装位置参考

安装位置由各平台自行决定，以下是常见参考：

| 平台 | 推荐安装目录 |
|------|-------------|
| Claude Code (macOS/Linux) | `~/.agents/skills/<name>/` |
| Claude Code (Windows) | `%USERPROFILE%\.agents\skills\<name>\` |
| OClaw | 由 OClaw 平台配置决定 |
| Qoder | 由 Qoder 平台配置决定 |

安装器不强制任何位置，只负责把 `.skill` 解压到指定目录并触发后续安装步骤。
