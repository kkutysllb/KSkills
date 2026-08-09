#!/bin/sh
# Uninstall script for docx
set -e

echo "→ Uninstalling docx..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  docx uninstalled successfully."
