#!/bin/sh
# Uninstall script for pptx
set -e

echo "→ Uninstalling pptx..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  pptx uninstalled successfully."
