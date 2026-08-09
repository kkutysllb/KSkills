#!/bin/sh
# Uninstall script for mcp-builder
set -e

echo "→ Uninstalling mcp-builder..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  mcp-builder uninstalled successfully."
