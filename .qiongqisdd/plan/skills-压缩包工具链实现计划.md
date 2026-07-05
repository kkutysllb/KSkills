# KSkills 压缩包工具链 — 实现计划（终稿）

## 目标

把 KSkills 的 `.skill` 压缩包生命周期打通为一条端到端工具链：**打包 → 校验 → 安装 → 卸载**，并补齐缺失环节（卸载脚本、端到端测试），使流程自洽、可测试、与现有脚本约定一致。

## 现状盘点（已核实）

已存在并工作的脚本：

| 脚本 | 行数 | 状态 | 关键能力 |
|------|------|------|---------|
| `scripts/validate_skills.py` | 11386B | ✅ 工作中 | 解析 frontmatter、字段校验、`parse_frontmatter`/`validate_file`/`SEV_*` |
| `scripts/build_skill.py` | 328 行 | ✅ 工作中 | 单技能打包为 `.skill` zip，生成 `SKILL-MANIFEST.json`（含 sha256），版本 `1.0.0` |
| `scripts/install_skill.sh` | 291 行 | ✅ 工作中 | `--list`/`--verify`/安装三种模式，sha256 校验，环境变量检查，可选执行 `install.sh` |
| `scripts/install-hooks.{sh,py}` | — | ✅ 工作中 | git pre-commit 钩子 |

**已确认的缺口**：

1. **无卸载工具** — `scripts/uninstall_skill.sh` 不存在，README 也未文档化卸载流程。安装侧已有 `--force` 覆盖，但无显式卸载入口。
2. **无端到端集成测试** — `scripts/test_toolchain.sh` 不存在，缺少"打包→安装→校验→卸载"的冒烟测试。
3. **路径约定核查结论（无需改代码）** — `build_skill.py` 中只有 `kskills_version`（manifest 元数据字段），**没有** `~/.ksills`/`~/.kskills` 等历史拼写路径 bug。`install_skill.sh` 注释和报错信息已统一使用 `~/.agents/skills/`（如第 16/18/193 行）。因此"路径统一"不再是独立改动步骤，只需让新增的 `uninstall_skill.sh` 默认值与之一致即可。

**关键结构事实**：

- **无 `skills/` 目录** — 技能直接存放在顶层分类目录下：`coding/`、`stock/`、`common/`、`media/`、`research/`。
- 内置最小示例技能候选：`common/md-to-html-converter/`、`common/chart-visualization/`、`common/analysis-report/`（均含 `SKILL.md`）。
- 安装侧读取 `SKILL-MANIFEST.json` 的字段：`name`、`version`、`package_type`、`entry`、`requires.env`。卸载侧只需 `name`/`version`。

## 实现步骤

### 步骤 1：新增 `scripts/uninstall_skill.sh`

POSIX `sh`，与 `install_skill.sh` 同风格（同样的颜色/`info`/`ok`/`warn`/`err`/`require_cmd` 函数前缀）。

```
Usage:
  ./scripts/uninstall_skill.sh <skill-name> [target-dir] [--force]
  ./scripts/uninstall_skill.sh --list [target-dir]
  ./scripts/uninstall_skill.sh --help
```

行为：

- `--list [target-dir]`：列出 `target-dir`（默认 `~/.agents/skills/`）下已安装技能及其版本（遍历子目录读取 `SKILL-MANIFEST.json` 的 `name`/`version`）。无技能时输出友好提示并退出 0。
- 默认模式：检查 `target-dir/<skill-name>` 是否存在；
  - 存在 → 读取其 `SKILL-MANIFEST.json` 确认 `name` 匹配（防误删）；
  - 若目录下存在 `uninstall.sh`（技能自带清理脚本）→ 询问是否执行（与 install 侧 `install.sh` 对称；`KSKILLS_AUTO_INSTALL=1` 时自动执行）；
  - 非 `--force` 时交互确认删除（`KSKILLS_AUTO_INSTALL=1` 跳过确认）；
  - 删除 `rm -rf "$dest"`；
  - 输出成功摘要（技能名、原位置）。
- `--force`：跳过所有交互确认直接删除。
- 未找到技能 → `err` + 非零退出码 + 明确错误信息。
- `--help`：打印用法。

约束：

- `set -eu`；`require_cmd python3`（读 manifest 用）；开头 `#!/bin/sh`。
- **删除路径双重保护**：删除前断言 `$dest` 是 `target-dir` 的直接子目录、且其 manifest `name` 与传入 `<skill-name>` 一致；任何一项不符则报错退出，绝不执行 `rm -rf`。
- 颜色/工具函数定义复制自 `install_skill.sh`（保持视觉一致），不引入共享文件以免改动既有脚本。

### 步骤 2：端到端冒烟测试 `scripts/test_toolchain.sh`

新增只读+临时目录的集成脚本，验证完整链路（不污染用户环境）：

```
1. mktemp -d 建 TMP；trap 清理
2. 示例技能：common/md-to-html-converter （回退顺序：md-to-html-converter → chart-visualization → analysis-report）
3. python3 scripts/build_skill.py <example> -o "$TMP/dist"        → 断言 .skill 文件存在
4. ./scripts/install_skill.sh "$TMP/dist/<x>.skill" "$TMP/target" → 断言 target/<name>/ 存在 + SKILL-MANIFEST.json 存在
5. ./scripts/install_skill.sh "$TMP/dist/<x>.skill" --verify      → 断言 sha256 通过（退出 0）
6. KSKILLS_AUTO_INSTALL=1 ./scripts/uninstall_skill.sh <name> "$TMP/target" --force → 断言目录被移除
7. 故意篡改 manifest sha256 → --verify 应失败（退出非0）
8. 全过 → 退出 0；任一步失败 → 打印步骤名 + 退出 1
```

约束：全部在 `mktemp -d` 下进行；`trap 'rm -rf "$TMP"' EXIT`；不依赖网络；退出码语义清晰。脚本开头打印每步 PASS/FAIL 摘要。

### 步骤 3：README 文档更新

在 README 的「打包与分发」章节（当前约 181–257 行）补充：

- **卸载小节**（位于「安装」之后）：`uninstall_skill.sh` 的 `--list`/默认/`--force` 用法，对称于 install 用法。
- **端到端测试**：`./scripts/test_toolchain.sh` 运行说明。
- 「按技能类型区别」表格（249 行附近）补充一列或一行说明卸载复杂度。
- 明确写「安装目标目录由平台决定，约定示例为 `~/.agents/skills/`」（已部分存在，确保措辞统一）。

不改动 README 的「技能总览」「SKILL.md 规范」「校验」等无关章节。

## 测试与验证

- **脚本层验证（必跑）**：
  - `bash scripts/test_toolchain.sh` → 期望退出码 0。
  - 篡改 sha256 分支单独验证 → `--verify` 非零退出。
- **手动验证矩阵**：
  - `install --list` / `--verify` / 安装 / `--force` 覆盖（回归）
  - `uninstall --list` / 默认确认 / `--force` / 卸载不存在的技能（应报错退出）
  - `KSKILLS_AUTO_INSTALL=1` 对称驱动安装与卸载
  - 技能自带 `uninstall.sh` 时的执行/跳过询问
- **校验回归**：`python3 scripts/validate_skills.py` 仍全绿（不涉及该脚本，但跑一遍确认无副作用）。
- **可执行位**：`chmod +x scripts/uninstall_skill.sh scripts/test_toolchain.sh`。

## 风险与回滚

- **风险 1：`uninstall_skill.sh` 的 `rm -rf` 误删。** 缓解：严格限定路径为 `target-dir/<skill-name>` 直接子目录；删除前二次校验 manifest `name` 一致；`--force` 外默认交互确认；`set -eu` + 严格参数校验；不在脚本中展开用户输入做命令拼接。
- **风险 2：默认 `target-dir` 与某些用户既有安装位置不符。** 缓解：默认值仅为示例，`--list`/卸载均允许显式传 `target-dir` 覆盖；README 显式说明约定。
- **风险 3：示例技能在 `build_skill.py` 下校验失败导致测试脚本误报。** 缓解：测试脚本对示例技能回退顺序选择，并在 build 失败时给出明确诊断。
- **回滚**：所有改动为新增脚本 + README 文档补充，无对现有打包/安装核心逻辑的破坏性改动；回滚即删除新增脚本并还原 README 段落。

## 不做的事（明确边界）

- 不改动 `build_skill.py` 的打包格式与 manifest schema（已稳定 1.0.0）。
- 不改动 `install_skill.sh` 的安装/校验核心流程（只在测试脚本中以黑盒方式调用）。
- 不改动 `validate_skills.py`。
- 不引入新的运行时依赖（继续只用 `sh`/`python3`/`unzip`/`zip`/`rm`）。
- 不实现「全局注册表」（`registry.json` 类机制超出本次范围，README 已说明由平台扫描目录加载）。
- 不新增共享 shell 工具库文件（避免改动既有 install 脚本，保持卸载脚本自包含）。
