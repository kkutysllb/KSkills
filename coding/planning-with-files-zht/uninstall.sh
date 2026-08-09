#!/bin/sh
# Uninstall script for planning-with-files-zht
set -e

echo "→ Uninstalling planning-with-files-zht..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  planning-with-files-zht uninstalled successfully."
