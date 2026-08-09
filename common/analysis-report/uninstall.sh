#!/bin/sh
# Uninstall script for analysis-report
set -e

echo "→ Uninstalling analysis-report..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  analysis-report uninstalled successfully."
