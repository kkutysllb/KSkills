#!/bin/sh
# Uninstall script for webapp-testing
set -e

echo "→ Uninstalling webapp-testing..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  webapp-testing uninstalled successfully."
