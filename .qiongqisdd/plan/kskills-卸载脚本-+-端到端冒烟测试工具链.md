# KSkills 卸载脚本 + 端到端冒烟测试 — 实施计划

## 目标
1. 完善 `scripts/uninstall_skill.sh`（已起草，待加可执行位）。
2. 新增 `scripts/test_toolchain.sh`：端到端冒烟测试 `build → install → verify → uninstall`，并覆盖「篡改 sha256 校验失败」分支。
3. 让两个脚本可执行，并实跑 `test_toolchain.sh` 验证全链路。
4. README 补充卸载小节 + 端到端测试说明。
5. 回归 `validate_skills.py` 仍全绿。

## 当前状态（已查证事实）
- `scripts/uninstall_skill.sh` 已存在（10091 字节，`#!/bin/sh`，`set -eu`），逻辑完整：
  - `--list` / 默认卸载 / `--force` 三模式
  - 双重删除保护：①dest 必须是 target-dir 直接子目录（解析 real path 防符号链接）②manifest 的 name 字段必须与传入名一致
  - `KSKILLS_AUTO_INSTALL=1` 跳过交互确认
  - 存在 `uninstall.sh` 时询问/自动执行
- `scripts/test_toolchain.sh` 不存在，需新建。
- `scripts/uninstall_skill.sh` 无可执行位（`-rw-r--r--`），需 `chmod +x`。
- 依赖现状（影响实跑）：
  - `python3` 3.9.6 可用；`unzip`、`shasum`、`sha256sum` 可用。
  - **PyYAML 未安装** → `build_skill.py` 与 `validate_skills.py` 均报 `ERROR: PyYAML is required`，端到端实跑与回归前需 `pip3 install pyyaml`。
- 样本选型：`common/md-to-html-converter`（含 `name: md-to-html-converter` / `version: 1.0.0`，带 `install.sh` 与 `uninstall.sh`），最小且对称覆盖 install/uninstall 清理脚本路径。
- build 输出：`dist/<name>-<version>.skill`（zip），`SKILL-MANIFEST.json` 含每文件 `sha256`。
- install 侧已具备 `verify_manifest()`（sha256 校验）与 `--verify` 模式。

## 实施步骤

### 1. `scripts/uninstall_skill.sh`
- 现状脚本已满足设计（`--list`/默认/`--force`、双重保护、`KSKILLS_AUTO_INSTALL`），**无需改逻辑**。
- 仅需 `chmod +x scripts/uninstall_skill.sh`（步骤 3 统一执行）。
- 轻度审计项（可选）：`list` 模式遍历用 `"$TARGET_DIR"/*/`，空目录时 for 不执行（已由 `found` 计数兜底），无问题。

### 2. 新增 `scripts/test_toolchain.sh`（端到端冒烟测试）
用 `#!/bin/sh` + `set -eu`，与 `install_skill.sh`/`uninstall_skill.sh` 同风格（复用同套颜色/工具函数）。

**流程**：
1. **前置检查**：`require_cmd python3 unzip`；检查 PyYAML 是否可用（`python3 -c "import yaml"`），缺失则给出明确提示退出（非 0）。
2. **准备临时工作区**：`mktemp -d` → `WORK`；`TMP_TARGET="$WORK/target"`；`trap 'rm -rf "$WORK"' EXIT` 清理。
3. **定义 `fail()` 断言助手**：打印差异并 `exit 1`；`ok()` 打印通过项。
4. **build**：`python3 scripts/build_skill.py common/md-to-html-converter -o "$WORK/dist"`，断言产物 `$WORK/dist/md-to-html-converter-1.0.0.skill` 存在且 `unzip -Z1` 首层为 `md-to-html-converter/`。
5. **install**：`KSKILLS_AUTO_INSTALL=1 ./scripts/install_skill.sh "$WORK/dist/md-to-html-converter-1.0.0.skill" "$TMP_TARGET"`，断言 `$TMP_TARGET/md-to-html-converter/SKILL.md` 存在且 `SKILL-MANIFEST.json` 存在。
6. **verify**：`./scripts/install_skill.sh "$WORK/dist/md-to-html-converter-1.0.0.skill" --verify` 返回 0。
7. **list（uninstall 侧）**：`./scripts/uninstall_skill.sh --list "$TMP_TARGET"` 输出含 `md-to-html-converter`。
8. **篡改 sha256 失败分支**：
   - 复制产物到 `$WORK/tampered.skill`。
   - 用 `python3` 解压 → 修改某非 manifest 文件（如 `CHANGELOG.md` 追加一行）→ 重新打成同结构 zip（不改 manifest）。
   - 断言 `./scripts/install_skill.sh "$WORK/tampered.skill" --verify` 返回非 0（期望失败）。
9. **uninstall**：`KSKILLS_AUTO_INSTALL=1 ./scripts/uninstall_skill.sh md-to-html-converter "$TMP_TARGET" --force`，断言 `$TMP_TARGET/md-to-html-converter` 不再存在。
10. **总结**：全部通过打印绿色 `✅ 端到端冒烟测试全部通过`。

**安全/隔离**：所有写操作限定在 `$WORK`；不触碰 `~/.agents/skills` 或仓库源文件；`trap EXIT` 兜底清理。

### 3. 加可执行位并实跑
- `chmod +x scripts/uninstall_skill.sh scripts/test_toolchain.sh`
- 先 `pip3 install pyyaml`（满足 build/validate 依赖）。
- 实跑 `./scripts/test_toolchain.sh`，确认退出码 0 且各阶段断言通过。

### 4. README
- 新增「卸载技能」小节：`--list` / 默认卸载 / `--force` / `KSKILLS_AUTO_INSTALL` 用法与双重保护说明。
- 新增「端到端测试」小节：`./scripts/test_toolchain.sh` 用途、前置依赖（PyYAML、unzip）、覆盖路径（build→install→verify→uninstall + 篡改分支）。

### 5. 回归
- `python3 scripts/validate_skills.py` 全绿（依赖步骤 3 的 PyYAML 安装）。

## 验证标准（完成判定）
- [ ] `test -x scripts/uninstall_skill.sh && test -x scripts/test_toolchain.sh`
- [ ] `./scripts/test_toolchain.sh` 退出码 0，断言全过
- [ ] 篡改 sha256 分支确认 install --verify 返回非 0
- [ ] `python3 scripts/validate_skills.py` 无 ERROR
- [ ] README 含卸载与端到端测试两小节

## 风险与备注
- **PyYAML 缺失**：当前环境未装，必须先 `pip3 install pyyaml`，否则 build/validate 无法运行 → 端到端无法验证。脚本内已做检测并给出明确提示。
- **macOS 默认 `python3` 为系统 3.9.6**：`pip3 install --user pyyaml` 可能需 `--user`；若遇 externally-managed 报错，改用 `pip3 install --break-system-packages pyyaml` 或 venv。
- **篡改分支 zip 重打**：必须保持与原包相同的 arcname 结构（`<skill_name>/<rel>`），否则 sha256 比对路径会失配，可能产生误报。重打逻辑用 python `zipfile`，`ZIP_DEFLATED`，逐文件按原 arcname 写入，仅替换目标文件内容。
- **`install.sh` 副作用**：样本 `md-to-html-converter/install.sh` 在 `KSKILLS_AUTO_INSTALL=1` 下会被执行；冒烟测试用隔离 `$TMP_TARGET`，避免污染真实环境。若该 install.sh 有网络/pip 操作，可能拖慢或失败 → 实跑时观察，必要时改选无 install.sh 的样本（如 `common/chart-visualization` 亦有 install.sh；若均失败则用 `analysis-report` 等无 install.sh 项，但需确认 uninstall.sh 路径覆盖减弱）。
- 严格只新增 `test_toolchain.sh` + chmod + README 编辑，不改 `install_skill.sh`/`build_skill.py`/`validate_skills.py` 既有行为。
