#!/bin/sh
# bump-version.sh — KSkills 版本号管理脚本
#
# 功能：
#   1. 读取 scripts/build_skill.py 中的 KSKILLS_VERSION
#   2. 支持 bump major / minor / patch 或指定显式版本号
#   3. --dry-run 预览模式（不修改文件）
#   4. --commit 自动 git commit
#   5. current 子命令显示当前版本
#
# Usage:
#   ./scripts/bump-version.sh current          # 显示当前版本号
#   ./scripts/bump-version.sh patch            # 1.0.0 → 1.0.1
#   ./scripts/bump-version.sh minor            # 1.0.0 → 1.1.0
#   ./scripts/bump-version.sh major            # 1.0.0 → 2.0.0
#   ./scripts/bump-version.sh 2.5.0            # 显式指定版本
#   ./scripts/bump-version.sh minor --dry-run  # 预览模式
#   ./scripts/bump-version.sh minor --commit   # bump + git commit
#
# 依赖：
#   - sed (POSIX)
#   - grep
#
# 设计说明：
#   - 核心版本号存在 scripts/build_skill.py: KSKILLS_VERSION = "X.Y.Z"
#   - 只在那一处维护，其他地方通过 manifest 或构建产物引用

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_PY="$SCRIPT_DIR/build_skill.py"

# ── 颜色 ──────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; CYAN=''; BOLD=''; NC=''
fi
info()  { printf "${CYAN}→${NC} %s\n" "$*"; }
ok()    { printf "${GREEN}✓${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}⚠${NC}  %s\n" "$*"; }
err()   { printf "${RED}✗${NC} %s\n" "$*" >&2; }

# ── 辅助函数 ──────────────────────────────────────────────────────────────────

# 从 build_skill.py 中解析当前版本
get_current_version() {
    grep -E '^KSKILLS_VERSION\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"' "$BUILD_PY" \
        | sed -E 's/^KSKILLS_VERSION[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/'
}

# semver 正则验证
valid_semver() {
    echo "$1" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'
}

# bump 逻辑
bump_version() {
    current="$1"
    part="$2"
    major="$(echo "$current" | cut -d. -f1)"
    minor="$(echo "$current" | cut -d. -f2)"
    patch="$(echo "$current" | cut -d. -f3)"
    case "$part" in
        major) echo "$((major + 1)).0.0" ;;
        minor) echo "$major.$((minor + 1)).0" ;;
        patch) echo "$major.$minor.$((patch + 1))" ;;
        *) err "未知 bump 类型：$part（支持：major, minor, patch）"; exit 1 ;;
    esac
}

# ── 主逻辑 ────────────────────────────────────────────────────────────────────

# 检查 build_skill.py 是否存在
[ -f "$BUILD_PY" ] || { err "找不到 $BUILD_PY"; exit 1; }

CURRENT_VERSION="$(get_current_version)"
[ -n "$CURRENT_VERSION" ] || { err "无法从 build_skill.py 解析版本号"; exit 1; }

# 子命令：current
if [ "${1:-}" = "current" ]; then
    echo "$CURRENT_VERSION"
    exit 0
fi

# 解析参数
DRY_RUN=false
COMMIT=false
VERSION_ARG="${1:-}"

shift 1 2>/dev/null || true
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --commit)  COMMIT=true ;;
        *) err "未知参数：$1（支持：--dry-run, --commit）"; exit 1 ;;
    esac
    shift
done

# 确定新版本
if [ -z "$VERSION_ARG" ]; then
    err "用法：$0 <major|minor|patch|X.Y.Z> [--dry-run] [--commit]"
    err "  $0 current  — 显示当前版本"
    exit 1
fi

if valid_semver "$VERSION_ARG"; then
    NEW_VERSION="$VERSION_ARG"
else
    case "$VERSION_ARG" in
        major|minor|patch)
            NEW_VERSION="$(bump_version "$CURRENT_VERSION" "$VERSION_ARG")"
            ;;
        *)
            err "无效版本号或 bump 类型：$VERSION_ARG"
            err "支持：major, minor, patch, 或合法 semver（如 2.0.0）"
            exit 1
            ;;
    esac
fi

# 验证新版本也是合法 semver
valid_semver "$NEW_VERSION" || { err "生成的新版本无效：$NEW_VERSION"; exit 1; }

ok "当前版本：$CURRENT_VERSION"
info "新版本：$NEW_VERSION"

if [ "$DRY_RUN" = true ]; then
    info "（dry-run 模式：未修改文件）"
    info "将会修改：$BUILD_PY"
    info "  KSKILLS_VERSION = \"$CURRENT_VERSION\" → \"$NEW_VERSION\""
    if [ "$COMMIT" = true ]; then
        info "  将会 git commit -m \"chore: bump version to $NEW_VERSION\""
    fi
    exit 0
fi

# 写入新版本
sed -i '' -E "s/^(KSKILLS_VERSION[[:space:]]*=[[:space:]]*\")[^\"]+(\".*)/\1$NEW_VERSION\2/" "$BUILD_PY" 2>/dev/null || \
sed -i -E "s/^(KSKILLS_VERSION[[:space:]]*=[[:space:]]*\")[^\"]+(\".*)/\1$NEW_VERSION\2/" "$BUILD_PY"

# 验证写入结果
UPDATED_VERSION="$(get_current_version)"
if [ "$UPDATED_VERSION" != "$NEW_VERSION" ]; then
    err "版本写入验证失败：期望 $NEW_VERSION，实际写入 $UPDATED_VERSION"
    exit 1
fi

ok "已更新 $BUILD_PY：$CURRENT_VERSION → $NEW_VERSION"

# Git commit
if [ "$COMMIT" = true ]; then
    cd "$(dirname "$BUILD_PY")/.."
    if ! git diff --quiet "$BUILD_PY"; then
        git add "$BUILD_PY"
        git commit -m "chore: bump version to $NEW_VERSION"
        ok "已 git commit：chore: bump version to $NEW_VERSION"
    else
        warn "无变更（文件未修改），跳过 git commit"
    fi
fi
