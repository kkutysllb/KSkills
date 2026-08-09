#!/bin/sh
# Uninstall script for planning-with-files-ar
set -e

echo "→ Uninstalling planning-with-files-ar..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  planning-with-files-ar uninstalled successfully."
