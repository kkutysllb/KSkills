#!/bin/sh
# Uninstall script for planning-with-files-de
set -e

echo "→ Uninstalling planning-with-files-de..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  planning-with-files-de uninstalled successfully."
