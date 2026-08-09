#!/bin/sh
# Uninstall script for pdf
set -e

echo "→ Uninstalling pdf..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  pdf uninstalled successfully."
