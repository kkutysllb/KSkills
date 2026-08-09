#!/bin/sh
# Uninstall script for planning-with-files-zh
set -e

echo "→ Uninstalling planning-with-files-zh..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  planning-with-files-zh uninstalled successfully."
