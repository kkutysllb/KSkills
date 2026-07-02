#!/bin/sh
# Install KSkills git hooks
#
# Usage:  sh scripts/install-hooks.sh

set -e

HOOKS_DIR=".githooks"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "✗ $HOOKS_DIR not found. Run from repository root."
    exit 1
fi

echo "→ Installing KSkills git hooks from $HOOKS_DIR ..."

git config core.hooksPath "$HOOKS_DIR"

echo "  ✓  Hooks installed. Git will now use $HOOKS_DIR/ as hooks directory."
echo ""
echo "     To bypass validation on a single commit:"
echo "       SKIP_VALIDATION=1 git commit"
echo ""
echo "     To revert to default hooks:"
echo "       git config --unset core.hooksPath"
