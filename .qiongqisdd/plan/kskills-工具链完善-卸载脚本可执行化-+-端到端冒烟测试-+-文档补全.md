# KSkills 工具链完善：卸载脚本可执行化 + 端到端冒烟测试 + 文档补全

## 背景与当前状态（已核实）

- `scripts/uninstall_skill.sh` **已创建**（270 行，内容完整：`--list` / `--force` / 双重删除保护 / `KSKILLS_AUTO_INSTALL` 支持），但**缺少可执行位**（当前 `-rw-r--r--`）。
- `scripts/test_toolchain.sh` **不存在**，需新建。
- `dist/` 为空，仓库内尚无已构建的 `.skill` 包。
- **PyYAML 不可用**：`python3 -c "import yaml"` 报 `ModuleNotFoundError`。
  - `validate_skills.py` 在 `import yaml` 外有 `try/except` 兜底（graceful degrade），但**启用深度 frontmatter 校验时需要 PyYAML**。
  - `build_skill.py` 打包默认开启 validate（需 PyYAML）；冒烟测试必须用 `--no-validate` 跳过，或安装 PyYAML。
- `install_skill.sh` 关键约定（已读源码核实）：
  - `KSKILLS_AUTO_INSTALL=1` 跳过交互确认、自动执行 `install.sh`。
  - `--verify` 模式：zip 完整性 + manifest 内 `sha256` 逐文件校验，失败 `exit 1`。
  - 校验失败时退出码为 `1`（install 与 verify 模式一致）。
- `uninstall_skill.sh` 关键约定（已读源码核实）：
  - 双重保护①：`dest` 必须是 `target-dir` 的**真实直接子目录**（`pwd -P` 解析，防符号链接绕过）。
  - 双重保护②：若存在 `SKILL-MANIFEST.json`，其 `name` 字段必须与传入 `SKILL_NAME` 一致。
  - 非 `--force` 且非 `auto` 模式：要求用户**输入完整技能名**确认（交互测试需用 `--force` 或 `KSKILLS_AUTO_INSTALL=1`）。
- README 现有结构：打包（185）、安装（205）、SKILL-MANIFEST.json（228）。**无卸载小节、无端到端测试说明**。

---

## 实施步骤

### 步骤 1：补齐 `uninstall_skill.sh` 可执行位（Todo #1 收尾）

```bash
chmod +x scripts/uninstall_skill.sh
# 验证：ls -la scripts/uninstall_skill.sh 应显示 -rwxr-xr-x
```

**风险**：无。该脚本内容已完整，仅缺权限位。

### 步骤 2：新建 `scripts/test_toolchain.sh`（Todo #2）

端到端冒烟测试脚本，覆盖 **build → verify → install → uninstall** 全链路 + **篡改 sha256 失败分支**。

#### 设计要点
- 用 `mktemp -d` 建临时工作区（`TMPTMP`），`trap 'rm -rf "$TMPTMP"' EXIT` 保证清理。
- 选一个**小且无重依赖**的内置技能做样本：候选 `stock/kk-earnings-forecast` 或 `stock/kk-valuation-model`（4 文件、无 install.sh 即可，减少副作用）。先 `ls` 确认候选技能结构，优先选**有 `install.sh` 但 `install.sh` 无副作用**或**无 `install.sh`** 的技能。
- 构造阶段：
  ```sh
  REPO=$(pwd)
  WORK=$(mktemp -d)
  TARGET="$WORK/skills"          # 模拟 ~/.agents/skills/
  mkdir -p "$TARGET"
  ```
- **PyYAML 缺失适配**：打包命令用 `--no-validate`（避免 frontmatter 深度校验依赖 PyYAML）：
  ```sh
  python3 "$REPO/scripts/build_skill.py" "$SKILL_DIR" -o "$WORK/dist" --no-validate
  ```
  > 注释说明：`--no-validate` 仅因本机 PyYAML 缺失；若环境装了 PyYAML 可去掉此 flag 做更严格校验。
- 构建：断言 `dist/<name>-<version>.skill` 存在，否则 `exit 1`。
- 安装前查看：`install_skill.sh <pkg>.skill --list` 与 `--verify`（期望均 `exit 0`）。
- 安装：`KSKILLS_AUTO_INSTALL=1 install_skill.sh <pkg>.skill "$TARGET/"`，断言 `exit 0` 且 `$TARGET/<name>/SKILL.md` 存在。
- 列出已安装：`uninstall_skill.sh --list "$TARGET/"`，断言输出含技能名。
- 卸载：`KSKILLS_AUTO_INSTALL=1 uninstall_skill.sh <name> "$TARGET/" --force`，断言 `exit 0` 且 `$TARGET/<name>` 已删除。
- **失败分支（篡改 sha256）**：
  ```sh
  # 复制一份包，解压、改 SKILL.md 内容、重新打包，制造 sha256 不匹配
  cp "$PKG" "$WORK/tampered.skill"
  TAMPER_DIR="$WORK/tampered_extract"
  mkdir -p "$TAMPER_DIR"
  unzip -q "$WORK/tampered.skill" -d "$TAMPER_DIR"
  echo "# TAMPERED" >> "$TAMPER_DIR/$NAME/SKILL.md"
  ( cd "$TAMPER_DIR" && zip -q -r "$WORK/tampered.skill" . )
  # 期望 --verify 失败（exit 1）
  if install_skill.sh "$WORK/tampered.skill" --verify >/dev/null 2>&1; then
      fail "篡改后的包应校验失败，但 --verify 返回 0"
  else
      pass "篡改检测：--verify 正确拒绝被篡改的包"
  fi
  ```
- 辅助函数：`pass()` / `fail()` / `info()`，`fail` 时 `exit 1`。
- 退出：全绿则 `exit 0` 并打印汇总 `✅ 端到端冒烟测试全部通过`。
- shebang 用 `#!/bin/sh`（与 `install_skill.sh`/`uninstall_skill.sh` 一致，POSIX 可移植）。
- `set -eu` 启用严格模式。

#### 脚本骨架
```sh
#!/bin/sh
# test_toolchain.sh — KSkills 工具链端到端冒烟测试
# 覆盖：build → verify → install → uninstall + 篡改 sha256 失败分支
set -eu

REPO=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
TARGET="$WORK/skills"
mkdir -p "$TARGET"
trap 'rm -rf "$WORK"' EXIT INT TERM

# 候选样本技能（小、低依赖）
SKILL_DIR="$REPO/stock/kk-earnings-forecast"   # 实施前 ls 再确认
# ... 各阶段断言 + 篡改分支 ...
```

### 步骤 3：chmod +x 并实跑验证（Todo #3）

```bash
chmod +x scripts/test_toolchain.sh
./scripts/test_toolchain.sh
```

**必须实跑**（符合"never claim verified without running"约束）。若 `--no-validate` 仍因缺 PyYAML 失败，回退方案：
1. 优先：`pip3 install --user pyyaml` 后去掉 `--no-validate`（更严格）。
2. 兜底：保留 `--no-validate`，并在脚本注释说明原因。

### 步骤 4：README 补充卸载小节 + 端到端测试说明（Todo #4）

在 README 现有 `### 安装`（约 205 行）之后、`### SKILL-MANIFEST.json`（约 228 行）之前插入：

```markdown
### 卸载

卸载已安装的技能，删除前有双重保护：
- 目标必须是 `target-dir` 的**直接子目录**（防符号链接绕过）
- 若存在 `SKILL-MANIFEST.json`，其 `name` 字段必须与传入名称一致

```sh
# 列出已安装技能
./scripts/uninstall_skill.sh --list ~/.agents/skills/

# 卸载指定技能（交互确认）
./scripts/uninstall_skill.sh md-to-html-converter ~/.agents/skills/

# 强制卸载（跳过确认）
./scripts/uninstall_skill.sh md-to-html-converter ~/.agents/skills/ --force

# 非交互模式（CI）
KSKILLS_AUTO_INSTALL=1 ./scripts/uninstall_skill.sh foo ~/.agents/skills/ --force
```

若技能目录含 `uninstall.sh`，会先询问是否执行（清理运行时依赖）。

### 端到端冒烟测试

验证 build → verify → install → uninstall 全链路，含篡改 sha256 失败分支：

```sh
./scripts/test_toolchain.sh
```
```

### 步骤 5：回归 `validate_skills.py`（Todo #5）

```bash
python3 scripts/validate_skills.py
```

- 期望：全绿（PyYAML 缺失时走 graceful degrade 分支）。
- 若因 PyYAML 报错，记录为**环境问题**而非脚本缺陷（脚本本身已 try/except 兜底）。

---

## 验收标准（Definition of Done）

1. ✅ `ls -la scripts/uninstall_skill.sh` 显示 `-rwxr-xr-x`
2. ✅ `ls -la scripts/test_toolchain.sh` 显示 `-rwxr-xr-x` 且存在
3. ✅ `./scripts/test_toolchain.sh` 实跑 `exit 0`，输出含 `✅ 端到端冒烟测试全部通过`，篡改分支被正确拒绝
4. ✅ README 含「卸载」「端到端冒烟测试」两个小节
5. ✅ `python3 scripts/validate_skills.py` 仍全绿

---

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| PyYAML 缺失导致 `build_skill.py` 默认校验失败 | 测试脚本用 `--no-validate`；注释说明可装 PyYAML 启用严格校验 |
| 候选技能含 `install.sh` 有副作用（如写 HOME） | 实施前先 `cat` 候选技能的 `install.sh`；优先选无副作用的；`KSKILLS_AUTO_INSTALL` 会自动执行 install.sh，需确认其无害 |
| `uninstall_skill.sh` 交互确认卡住测试 | 测试中统一用 `KSKILLS_AUTO_INSTALL=1 ... --force` 跳过 |
| 篡改分支的 zip 重打包导致 manifest 的 sha256 与新文件不匹配的逻辑偏差 | 先手动验证一次：篡改后 `--verify` 必须 `exit 1`；这是 install 脚本既有行为，测试只是断言它 |
| 临时目录残留 | `trap 'rm -rf "$WORK"' EXIT INT TERM` |

---

## 不在范围内

- 不修改 `build_skill.py` / `install_skill.sh` / `validate_skills.py` 的既有逻辑（仅调用它们）。
- 不安装 PyYAML 作为项目硬依赖（仅文档说明可选）。
- 不改技能仓库内任何 `SKILL.md` / `install.sh` / `uninstall.sh`。
