#!/bin/sh
# Uninstall script for kk-music-generation
set -e

echo "→ Uninstalling kk-music-generation..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  kk-music-generation uninstalled successfully."
