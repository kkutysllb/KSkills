#!/bin/sh
# install_skill.sh — 从 .skill 压缩包安装技能
#
# 设计原则：
#   1. 不假设安装位置 — 由调用方/平台通过参数或环境变量指定
#   2. 安装前先校验压缩包完整性和 manifest
#   3. 若存在 install.sh，询问是否执行（安装 Python 依赖等）
#   4. 检查 permissions.env 声明的环境变量是否已设置
#
# Usage:
#   ./scripts/install_skill.sh <package.skill> [target-dir] [--force]
#   ./scripts/install_skill.sh <package.skill> --list
#   ./scripts/install_skill.sh <package.skill> --verify
#
# Examples:
#   ./scripts/install_skill.sh dist/kk-business-query-1.0.0.skill ~/.agents/skills/
#   ./scripts/install_skill.sh dist/kk-business-query-1.0.0.skill --list
#   KSKILLS_AUTO_INSTALL=1 ./scripts/install_skill.sh dist/foo.skill ~/.agents/skills/

set -eu

# ── 颜色与工具函数 ────────────────────────────────────────────────────────────
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

# KSKILLS_AUTO_INSTALL=1 时跳过所有交互式询问，直接执行 install.sh
auto_install=${KSKILLS_AUTO_INSTALL:-0}

# ── 依赖检查 ──────────────────────────────────────────────────────────────────
require_cmd() {
    command -v "$1" > /dev/null 2>&1 || { err "缺少依赖：$1（请先安装）"; exit 1; }
}
require_cmd unzip
require_cmd python3

# ── 参数解析 ──────────────────────────────────────────────────────────────────
PACKAGE=""
TARGET_DIR=""
MODE="install"   # install | list | verify
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --list)   MODE="list"; shift ;;
        --verify) MODE="verify"; shift ;;
        --force)  FORCE=1; shift ;;
        -h|--help)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *)
            if [ -z "$PACKAGE" ]; then
                PACKAGE="$1"
            elif [ -z "$TARGET_DIR" ]; then
                TARGET_DIR="$1"
            else
                err "未知参数：$1"; exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$PACKAGE" ]; then
    err "用法：$0 <package.skill> [target-dir] [--force|--list|--verify]"
    exit 1
fi

if [ ! -f "$PACKAGE" ]; then
    err "文件不存在：$PACKAGE"
    exit 1
fi

# ── 提取技能名（压缩包内顶层目录）────────────────────────────────────────────
# .skill 包的顶层目录名即技能名（打包时以技能目录为根）
skill_name=$(unzip -Z1 "$PACKAGE" 2>/dev/null | head -1 | cut -d'/' -f1)
if [ -z "$skill_name" ]; then
    err "无法读取包内容（可能不是有效的 zip）"
    exit 1
fi

# ══════════════════════════════════════════════════════════════════════════════
# 模式：--list  仅列出包内容
# ══════════════════════════════════════════════════════════════════════════════
if [ "$MODE" = "list" ]; then
    printf "${BOLD}📦 %s${NC}\n\n" "$PACKAGE"
    unzip -l "$PACKAGE"
    # 尝试显示 manifest 摘要
    manifest_path="${skill_name}/SKILL-MANIFEST.json"
    if unzip -l "$PACKAGE" 2>/dev/null | grep -q "SKILL-MANIFEST.json"; then
        printf "\n${BOLD}📋 Manifest 摘要${NC}\n"
        unzip -p "$PACKAGE" "$manifest_path" 2>/dev/null | python3 -c '
import json, sys
try:
    m = json.load(sys.stdin)
    def g(k): return m.get(k) or "?"
    print("  name         :", g("name"))
    print("  version      :", g("version"))
    print("  category     :", g("category"))
    print("  package_type :", g("package_type"))
    if m.get("entry"):
        print("  entry        :", m["entry"])
    req = m.get("requires") or {}
    pkgs = req.get("packages") or []
    env = req.get("env") or []
    if pkgs: print("  packages     :", ", ".join(pkgs))
    if env:  print("  env vars     :", ", ".join(env))
except Exception as e:
    print("  (无法解析 manifest:", e, ")")
'
    fi
    exit 0
fi

# ══════════════════════════════════════════════════════════════════════════════
# 校验阶段（install 和 verify 模式都需要）
# ══════════════════════════════════════════════════════════════════════════════
info "校验压缩包完整性..."
if ! unzip -t "$PACKAGE" > /dev/null 2>&1; then
    err "压缩包损坏或不是有效的 zip"
    exit 1
fi
ok "压缩包完整"

# manifest sha256 校验（如果包内有 manifest）
verify_manifest() {
    manifest_path="${skill_name}/SKILL-MANIFEST.json"
    if ! unzip -l "$PACKAGE" 2>/dev/null | grep -q "SKILL-MANIFEST.json"; then
        warn "包内无 SKILL-MANIFEST.json，跳过 sha256 校验"
        return 0
    fi

    info "校验文件 sha256..."
    local tmpdir
    tmpdir=$(mktemp -d)
    trap 'rm -rf "$tmpdir"' RETURN

    if ! unzip -q "$PACKAGE" -d "$tmpdir" 2>/dev/null; then
        err "解压失败（用于校验）"
        return 1
    fi

    # 用 python 校验 sha256（跨平台）
    python3 - "$tmpdir/$manifest_path" "$tmpdir/$skill_name" <<'PYEOF' || return 1
import json, hashlib, sys, os
manifest_path, skill_root = sys.argv[1], sys.argv[2]
with open(manifest_path, encoding="utf-8") as f:
    m = json.load(f)
errors = 0
for entry in m.get("files", []):
    p, expected = entry["path"], entry["sha256"]
    full = os.path.join(os.path.dirname(skill_root), p)  # arcname 以技能名为根
    # arcname 形如 "<skill_name>/<relative>"，skill_root 已是 .../<skill_name>
    full = os.path.join(skill_root, os.path.relpath(p, m["name"]))
    if not os.path.isfile(full):
        print(f"  ✗ 缺失：{p}")
        errors += 1
        continue
    actual = hashlib.sha256(open(full, "rb").read()).hexdigest()
    if actual != expected:
        print(f"  ✗ 校验失败：{p}")
        errors += 1
sys.exit(1 if errors else 0)
PYEOF
    ok "sha256 校验通过"
    return 0
}

if ! verify_manifest; then
    err "manifest 校验失败"
    [ "$MODE" = "verify" ] && exit 1 || exit 1
fi

if [ "$MODE" = "verify" ]; then
    ok "✅ $PACKAGE 校验通过"
    exit 0
fi

# ══════════════════════════════════════════════════════════════════════════════
# 安装阶段
# ══════════════════════════════════════════════════════════════════════════════
if [ -z "$TARGET_DIR" ]; then
    err "未指定目标目录。用法：$0 <package.skill> <target-dir>"
    err "目标目录由调用平台决定，例如：~/.agents/skills/"
    exit 1
fi

# 展开目标目录中的 ~
TARGET_DIR=$(eval echo "$TARGET_DIR")
dest="$TARGET_DIR/$skill_name"

# 冲突检查
if [ -d "$dest" ] && [ "$FORCE" -ne 1 ]; then
    err "目标已存在：$dest"
    err "使用 --force 覆盖，或先卸载旧版本"
    exit 1
fi

if [ -d "$dest" ]; then
    warn "覆盖已有目录：$dest"
    rm -rf "$dest"
fi

mkdir -p "$TARGET_DIR"
info "解压到 $dest ..."
unzip -q "$PACKAGE" -d "$TARGET_DIR"
# zip 解压后会在 target 下生成 <skill_name>/ 目录
ok "已解压到 $dest"

# 读取 manifest 获取包类型和依赖信息
pkg_type=""
env_vars=""
entry=""
if [ -f "$dest/SKILL-MANIFEST.json" ]; then
    manifest_info=$(python3 - "$dest/SKILL-MANIFEST.json" <<'PYEOF'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
pkg_type = m.get("package_type") or ""
entry = m.get("entry") or ""
env = (m.get("requires") or {}).get("env") or []
# 输出为 shell 安全的赋值
print("pkg_type=" + repr(pkg_type))
print("entry=" + repr(entry))
print("env_vars=" + repr(" ".join(env)))
PYEOF
    ) || true
    eval "$manifest_info"
fi

# 检查环境变量
if [ -n "$env_vars" ]; then
    printf "\n${BOLD}🔍 环境变量检查${NC}\n"
    missing=""
    for var in $env_vars; do
        eval "val=\${$var:-}"
        if [ -z "$val" ]; then
            warn "未设置：$var"
            missing="$missing $var"
        else
            ok "已设置：$var"
        fi
    done
    if [ -n "$missing" ]; then
        printf "  ${YELLOW}请设置以下变量后使用：${NC}\n"
        for var in $missing; do
            printf "    export %s=<your-key>\n" "$var"
        done
    fi
fi

# 执行 install.sh（如果存在）
if [ -f "$dest/install.sh" ]; then
    printf "\n${BOLD}🔧 安装脚本${NC}\n"
    if [ "$auto_install" = "1" ]; then
        run_it=1
    else
        printf "  发现 install.sh，是否执行？（将安装运行时依赖，Y/n）: "
        read -r answer
        case "$answer" in
            n|N) run_it=0 ;;
            *)   run_it=1 ;;
        esac
    fi

    if [ "$run_it" = "1" ]; then
        info "执行 $dest/install.sh ..."
        # install.sh 设计为在技能目录内运行
        ( cd "$dest" && sh ./install.sh ) || warn "install.sh 执行返回非零状态"
        ok "install.sh 执行完毕"
    else
        warn "已跳过 install.sh。后续可手动执行：cd $dest && sh ./install.sh"
    fi
fi

# 完成
printf "\n${GREEN}${BOLD}✅ 安装成功${NC}\n"
printf "  技能   : %s\n" "$skill_name"
printf "  位置   : %s\n" "$dest"
[ -n "$pkg_type" ] && printf "  类型   : %s\n" "$pkg_type"
[ -n "$entry" ]    && printf "  入口   : %s\n" "$entry"
printf "\n  下一步：平台（Claude Code / OClaw 等）会自动扫描 %s 下的 SKILL.md 并加载。\n" "$TARGET_DIR"
