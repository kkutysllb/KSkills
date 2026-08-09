#!/bin/sh
# Uninstall script for skill-creator
set -e

echo "→ Uninstalling skill-creator..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  skill-creator uninstalled successfully."
