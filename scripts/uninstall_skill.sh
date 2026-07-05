#!/bin/sh
# uninstall_skill.sh — 卸载已安装的 KSkills 技能
#
# 设计原则：
#   1. 不假设安装位置 — 由调用方/平台通过参数指定（默认 ~/.agents/skills/）
#   2. 删除前双重保护：目标是 target-dir 直接子目录 + manifest name 一致
#   3. 若存在 uninstall.sh，询问是否执行（对称于 install 侧的 install.sh）
#   4. 非 --force 时交互确认；KSKILLS_AUTO_INSTALL=1 跳过确认
#
# Usage:
#   ./scripts/uninstall_skill.sh <skill-name> [target-dir] [--force]
#   ./scripts/uninstall_skill.sh --list [target-dir]
#   ./scripts/uninstall_skill.sh --help
#
# Examples:
#   ./scripts/uninstall_skill.sh md-to-html-converter ~/.agents/skills/
#   ./scripts/uninstall_skill.sh --list ~/.agents/skills/
#   KSKILLS_AUTO_INSTALL=1 ./scripts/uninstall_skill.sh foo ~/.agents/skills/ --force

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

# KSKILLS_AUTO_INSTALL=1 时跳过所有交互式询问
auto_install=${KSKILLS_AUTO_INSTALL:-0}

# ── 依赖检查 ──────────────────────────────────────────────────────────────────
require_cmd() {
    command -v "$1" > /dev/null 2>&1 || { err "缺少依赖：$1（请先安装）"; exit 1; }
}
require_cmd python3

# ── 默认目标目录 ──────────────────────────────────────────────────────────────
# 约定示例：~/.agents/skills/（实际由调用平台决定）
DEFAULT_TARGET_DIR="$HOME/.agents/skills"

# ── 参数解析 ──────────────────────────────────────────────────────────────────
SKILL_NAME=""
TARGET_DIR=""
MODE="uninstall"   # uninstall | list
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --list)  MODE="list"; shift ;;
        --force) FORCE=1; shift ;;
        -h|--help)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *)
            if [ -z "$SKILL_NAME" ]; then
                SKILL_NAME="$1"
            elif [ -z "$TARGET_DIR" ]; then
                TARGET_DIR="$1"
            else
                err "未知参数：$1"; exit 1
            fi
            shift
            ;;
    esac
done

# 展开目标目录中的 ~ 和 环境变量；未指定则用默认
if [ -z "$TARGET_DIR" ]; then
    TARGET_DIR="$DEFAULT_TARGET_DIR"
else
    TARGET_DIR=$(eval echo "$TARGET_DIR")
fi

# ══════════════════════════════════════════════════════════════════════════════
# 模式：--list  列出已安装技能及其版本
# ══════════════════════════════════════════════════════════════════════════════
if [ "$MODE" = "list" ]; then
    if [ ! -d "$TARGET_DIR" ]; then
        info "目标目录不存在：$TARGET_DIR"
        info "（尚未安装任何技能）"
        exit 0
    fi
    printf "${BOLD}📦 %s 下已安装技能${NC}\n\n" "$TARGET_DIR"
    found=0
    # 遍历 target-dir 下的直接子目录
    for d in "$TARGET_DIR"/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        manifest="$d/SKILL-MANIFEST.json"
        if [ -f "$manifest" ]; then
            # 用 python 读取 name/version（跨平台）
            version=$(python3 - "$manifest" <<'PYEOF' 2>/dev/null || echo "?"
import json, sys
try:
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    print(m.get("version") or "?")
except Exception:
    print("?")
PYEOF
            )
            manifest_name=$(python3 - "$manifest" <<'PYEOF' 2>/dev/null || echo ""
import json, sys
try:
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    print(m.get("name") or "")
except Exception:
    print("")
PYEOF
            )
        else
            version="(无 manifest)"
            manifest_name=""
        fi
        if [ -n "$manifest_name" ] && [ "$manifest_name" != "$name" ]; then
            printf "  %-30s %s  ${YELLOW}(manifest name: %s)${NC}\n" "$name" "$version" "$manifest_name"
        else
            printf "  %-30s %s\n" "$name" "$version"
        fi
        found=1
    done
    if [ "$found" -eq 0 ]; then
        printf "  ${YELLOW}(无已安装技能)${NC}\n"
    fi
    exit 0
fi

# ══════════════════════════════════════════════════════════════════════════════
# 模式：uninstall  卸载指定技能
# ══════════════════════════════════════════════════════════════════════════════
if [ -z "$SKILL_NAME" ]; then
    err "用法：$0 <skill-name> [target-dir] [--force|--list]"
    exit 1
fi

# 安全校验：skill-name 不能含路径分隔符（防注入 / 误删上层目录）
case "$SKILL_NAME" in
    */*|*..*)
        err "技能名不能包含路径分隔符：$SKILL_NAME"
        err "（仅允许 target-dir 下的直接子目录名）"
        exit 1
        ;;
esac

# 规范化 target-dir（去尾部斜杠），构造 dest
target_norm="${TARGET_DIR%/}"
dest="$target_norm/$SKILL_NAME"

if [ ! -d "$target_norm" ]; then
    err "目标目录不存在：$target_norm"
    err "（请用 --list 查看已安装技能，或指定正确的 target-dir）"
    exit 1
fi

# 第一道保护：dest 必须是 target-dir 的直接子目录（不是符号链接、不指向其它位置）
if [ ! -d "$dest" ]; then
    err "未找到技能：$SKILL_NAME"
    err "位置：$dest"
    err "（用 --list 查看已安装技能列表）"
    exit 1
fi

# 解析真实路径，防止符号链接绕过
dest_real=$(cd "$dest" && pwd -P)
target_real=$(cd "$target_norm" && pwd -P)
# dest_real 的父目录必须等于 target_real
dest_parent=$(dirname "$dest_real")
if [ "$dest_parent" != "$target_real" ]; then
    err "安全检查失败：$SKILL_NAME 不在 $target_norm 的直接子目录下"
    err "  dest_real   = $dest_real"
    err "  dest_parent = $dest_parent"
    err "  target_real = $target_real"
    err "（拒绝执行删除，避免误删）"
    exit 1
fi

# 第二道保护：若存在 manifest，其 name 字段必须与传入 SKILL_NAME 一致
manifest="$dest/SKILL-MANIFEST.json"
if [ -f "$manifest" ]; then
    manifest_name=$(python3 - "$manifest" <<'PYEOF' 2>/dev/null || echo ""
import json, sys
try:
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    print(m.get("name") or "")
except Exception:
    print("")
PYEOF
    )
    if [ -n "$manifest_name" ] && [ "$manifest_name" != "$SKILL_NAME" ]; then
        err "manifest name 不匹配，拒绝删除（防误删）"
        err "  传入名称      : $SKILL_NAME"
        err "  manifest name : $manifest_name"
        err "  位置          : $dest"
        err "（如确需删除，请使用与 manifest 一致的名称）"
        exit 1
    fi
    # 顺便读取版本用于摘要
    manifest_version=$(python3 - "$manifest" <<'PYEOF' 2>/dev/null || echo "?"
import json, sys
try:
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    print(m.get("version") or "?")
except Exception:
    print("?")
PYEOF
    )
else
    manifest_version="(无 manifest)"
fi

ok "已定位技能：$SKILL_NAME (v$manifest_version)"
ok "位置：$dest"

# 执行技能自带的 uninstall.sh（如果存在）— 对称于 install 侧的 install.sh
if [ -f "$dest/uninstall.sh" ]; then
    printf "\n${BOLD}🧹 清理脚本${NC}\n"
    if [ "$auto_install" = "1" ]; then
        run_it=1
    else
        printf "  发现 uninstall.sh，是否执行？（将清理运行时依赖，Y/n）: "
        read -r answer
        case "$answer" in
            n|N) run_it=0 ;;
            *)   run_it=1 ;;
        esac
    fi

    if [ "$run_it" = "1" ]; then
        info "执行 $dest/uninstall.sh ..."
        # uninstall.sh 设计为在技能目录内运行
        ( cd "$dest" && sh ./uninstall.sh ) || warn "uninstall.sh 执行返回非零状态"
        ok "uninstall.sh 执行完毕"
    else
        warn "已跳过 uninstall.sh。后续可手动执行：cd $dest && sh ./uninstall.sh"
    fi
fi

# 交互确认（非 --force 时）
if [ "$FORCE" -ne 1 ] && [ "$auto_install" != "1" ]; then
    printf "\n${YELLOW}即将删除：${NC}%s\n" "$dest"
    printf "确认删除？（输入完整技能名 %s 确认 / 其它取消）: " "$SKILL_NAME"
    read -r confirm
    if [ "$confirm" != "$SKILL_NAME" ]; then
        err "已取消（输入不匹配）"
        exit 1
    fi
fi

# 执行删除（此时已通过双重保护）
info "删除 $dest ..."
rm -rf "$dest"

# 删除后验证：目录确实已不存在
if [ -d "$dest" ]; then
    err "删除失败：$dest 仍然存在"
    exit 1
fi

printf "\n${GREEN}${BOLD}✅ 卸载成功${NC}\n"
printf "  技能 : %s\n" "$SKILL_NAME"
[ "$manifest_version" != "(无 manifest)" ] && printf "  版本 : %s\n" "$manifest_version"
printf "  原位置 : %s\n" "$dest"
