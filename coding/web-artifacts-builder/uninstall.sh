#!/bin/sh
# Uninstall script for web-artifacts-builder
set -e

echo "→ Uninstalling web-artifacts-builder..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  web-artifacts-builder uninstalled successfully."
