#!/bin/sh
# Uninstall script for kk-image-generation
set -e

echo "→ Uninstalling kk-image-generation..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  kk-image-generation uninstalled successfully."
