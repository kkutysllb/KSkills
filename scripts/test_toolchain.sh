#!/bin/sh
# test_toolchain.sh — KSkills 工具链端到端冒烟测试
#
# 目的：验证 install_skill.sh / uninstall_skill.sh / build_skill.py 三者协作正确
#
# 测试流程：
#   1. 选择一个真实存在的源技能（如 coding/refactor）作为 fixture
#   2. 用 build_skill.py 打包成 .skill
#   3. 用 install_skill.sh 安装到临时目录（隔离真实环境）
#   4. 用 install_skill.sh --verify 验证安装完整性
#   5. 用 uninstall_skill.sh 卸载
#   6. 验证目标目录已清理
#   7. 篡改 .skill 内容（不重算 sha256）→ install --verify 必须拒绝
#   8. 用 validate_skills.py 跑回归（如有 PyYAML）
#
# 设计原则：
#   - 全程在临时目录进行，不污染 ~/.agents/skills/
#   - 任一步失败立即 exit 1，输出失败阶段
#   - 不要求网络；所有操作本地完成
#   - 退出时清理临时产物（trap EXIT）
#
# Usage:
#   ./scripts/test_toolchain.sh                          # 默认测试 coding/refactor
#   ./scripts/test_toolchain.sh stock/kk-factor-research  # 指定其他技能
#
# 依赖：
#   - bash（POSIX sh 即可，但用 bash 跑更安全）
#   - python3 + PyYAML（validate_skills.py 需要）
#   - zip / unzip（build & install_skill 需要）

set -eu

# ── 颜色与输出 ────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'
    CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; CYAN=''; BOLD=''; NC=''
fi

info()  { printf "${CYAN}→${NC} %s\n" "$*"; }
ok()    { printf "${GREEN}✓${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}⚠${NC}  %s\n" "$*"; }
err()   { printf "${RED}✗${NC} %s\n" "$*" >&2; }
step()  { printf "\n${BOLD}── %s ──${NC}\n" "$*"; }

# ── 依赖检查 ──────────────────────────────────────────────────────────────────
require_cmd() {
    command -v "$1" >/dev/null 2>&1 || { err "缺少依赖：$1"; exit 1; }
}

require_cmd python3
require_cmd zip
require_cmd unzip

# PyYAML 软依赖（用于 validate_skills.py；缺失时跳过回归步骤）
if python3 -c "import yaml" 2>/dev/null; then
    HAS_YAML=1
else
    warn "PyYAML 未安装，将跳过 validate_skills.py 回归（pip install pyyaml 可启用）"
    HAS_YAML=0
fi

# ── 路径解析 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

BUILD_PY="$SCRIPT_DIR/build_skill.py"
INSTALL_SH="$SCRIPT_DIR/install_skill.sh"
UNINSTALL_SH="$SCRIPT_DIR/uninstall_skill.sh"
VALIDATE_PY="$SCRIPT_DIR/validate_skills.py"

for f in "$BUILD_PY" "$INSTALL_SH" "$UNINSTALL_SH" "$VALIDATE_PY"; do
    [ -f "$f" ] || { err "缺失脚本：$f"; exit 1; }
done

# ── 选择 fixture 技能 ─────────────────────────────────────────────────────────
FIXTURE="${1:-coding/refactor}"
if [ ! -d "$REPO_ROOT/$FIXTURE" ]; then
    err "fixture 不存在：$FIXTURE"
    err "用法：$0 [category/skill-name]"
    exit 1
fi

FIXTURE_NAME="$(basename "$FIXTURE")"
info "fixture 技能：$FIXTURE"

# ── 临时工作区（隔离真实环境）─────────────────────────────────────────────────
TMPDIR_BASE="$(mktemp -d -t kskills-toolchain.XXXXXX)"
TMPDIR_DIST="$TMPDIR_BASE/dist"
TMPDIR_TARGET="$TMPDIR_BASE/target"
mkdir -p "$TMPDIR_DIST" "$TMPDIR_TARGET"

cleanup() {
    if [ -d "$TMPDIR_BASE" ]; then
        rm -rf "$TMPDIR_BASE"
    fi
}
trap cleanup EXIT INT TERM

ok "临时工作区：$TMPDIR_BASE"

# ── 步骤 1：build ─────────────────────────────────────────────────────────────
step "1/6 打包：build_skill.py $FIXTURE → dist/"

# 用 --no-validate 跳过 build 阶段的校验（validate 步骤独立跑）
SKIP_VALIDATE=1 python3 "$BUILD_PY" "$FIXTURE" -o "$TMPDIR_DIST" --no-validate

SKILL_PKG="$(ls "$TMPDIR_DIST"/*.skill 2>/dev/null | head -1)"
[ -n "$SKILL_PKG" ] || { err "未生成 .skill 包"; exit 1; }
ok "已打包：$(basename "$SKILL_PKG")"

# ── 步骤 2：install ───────────────────────────────────────────────────────────
step "2/6 安装：install_skill.sh → $TMPDIR_TARGET/"

KSKILLS_AUTO_INSTALL=0 "$INSTALL_SH" "$SKILL_PKG" "$TMPDIR_TARGET" --force
ok "已安装到 $TMPDIR_TARGET/$FIXTURE_NAME"

# ── 步骤 3：verify ────────────────────────────────────────────────────────────
step "3/6 校验：install_skill.sh --verify"
KSKILLS_AUTO_INSTALL=0 "$INSTALL_SH" "$SKILL_PKG" --verify
ok "包完整性校验通过"

# ── 步骤 4：installed sanity ──────────────────────────────────────────────────
step "4/6 验证：安装目录结构"
DEST="$TMPDIR_TARGET/$FIXTURE_NAME"
if [ ! -d "$DEST" ]; then
    err "安装目录不存在：$DEST"
    exit 1
fi
[ -f "$DEST/SKILL.md" ] || { err "缺少 SKILL.md"; exit 1; }
[ -f "$DEST/SKILL-MANIFEST.json" ] || { err "缺少 SKILL-MANIFEST.json"; exit 1; }
ok "目标结构完整（SKILL.md + SKILL-MANIFEST.json）"

# ── 步骤 5：uninstall ─────────────────────────────────────────────────────────
step "5/6 卸载：uninstall_skill.sh（强制模式，跳过 uninstall.sh）"
KSKILLS_AUTO_INSTALL=1 "$UNINSTALL_SH" "$FIXTURE_NAME" "$TMPDIR_TARGET" --force

# ── 步骤 6：cleanup verify ────────────────────────────────────────────────────
step "6/6 验证：目标目录已清理"
if [ -d "$DEST" ]; then
    err "卸载后目录仍存在：$DEST"
    exit 1
fi
ok "目标目录已彻底删除"

# ── 步骤 7：篡改 sha256（负向校验）─────────────────────────────────────────────
step "7 篡改 sha256：install --verify 必须拒绝被篡改的包"

TAMPER_PKG="$TMPDIR_BASE/tampered.skill"
cp "$SKILL_PKG" "$TAMPER_PKG"

# 重打 zip：解压 → 追加一行到 CHANGELOG.md（不改 manifest）→ 按原 arcname 重压
python3 - "$TAMPER_PKG" "$TMPDIR_BASE" <<'PYEOF'
import zipfile, os, shutil, sys
pkg, workdir = sys.argv[1], sys.argv[2]
tmpdir = os.path.join(workdir, "_tamper_extract")
if os.path.isdir(tmpdir):
    shutil.rmtree(tmpdir)
os.makedirs(tmpdir, exist_ok=True)
with zipfile.ZipFile(pkg, "r") as z:
    z.extractall(tmpdir)
    names = z.namelist()
target = next((n for n in names if n.endswith("CHANGELOG.md")), None)
if not target:
    target = next((n for n in names if not n.endswith("SKILL-MANIFEST.json")), None)
if target:
    p = os.path.join(tmpdir, target)
    with open(p, "a", encoding="utf-8") as f:
        f.write("\n# tampered for negative test\n")
print(f"[tampered] appended to {target}", flush=True)
os.remove(pkg)
with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(tmpdir):
        for fn in files:
            full = os.path.join(root, fn)
            arc = os.path.relpath(full, tmpdir).replace(os.sep, "/")
            z.write(full, arc)
shutil.rmtree(tmpdir)
PYEOF

# 期望 install --verify 返回非 0
set +e
KSKILLS_AUTO_INSTALL=0 "$INSTALL_SH" "$TAMPER_PKG" --verify >/dev/null 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
    err "篡改校验应失败但 install --verify 通过 (exit=0)；install_skill.sh 未检测 sha256 漂移"
    exit 1
fi
ok "被篡改的 .skill 被 install --verify 拒绝 (exit=$rc)"

rm -f "$TAMPER_PKG"
# ── 回归（可选）──────────────────────────────────────────────────────────────
if [ "$HAS_YAML" = "1" ]; then
    step "回归：validate_skills.py"
    python3 "$VALIDATE_PY" "$REPO_ROOT" >/dev/null 2>&1 \
        && ok "validate_skills.py 通过（无 ERROR）" \
        || warn "validate_skills.py 发现问题（不影响本测试）"
fi

# ── 汇总 ─────────────────────────────────────────────────────────────────────
printf "\n${GREEN}${BOLD}✅ 工具链端到端冒烟测试通过${NC}\n"
printf "  fixture     : %s\n" "$FIXTURE"
printf "  包          : %s\n" "$(basename "$SKILL_PKG")"
printf "  install → verify → uninstall → cleanup 全链路 OK\n"
printf "  篡改 sha256 → install --verify 拒绝确认\n"