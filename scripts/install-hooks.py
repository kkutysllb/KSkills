#!/usr/bin/env python3
"""
Install KSkills git hooks.
Cross-platform alternative to install-hooks.sh.

Usage:
    python3 scripts/install-hooks.py
"""

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_DIR = os.path.join(REPO_ROOT, ".githooks")


def main():
    if not os.path.isdir(HOOKS_DIR):
        print(f"✗ {HOOKS_DIR} not found. Run from repository root.")
        return 1

    print("→ Installing KSkills git hooks from .githooks/ ...")

    result = subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"✗ Failed: {result.stderr.strip()}")
        return 1

    print("  ✓  Hooks installed. Git will now use .githooks/ as hooks directory.")
    print()
    print("     To bypass validation on a single commit:")
    print("       SKIP_VALIDATION=1 git commit  (macOS/Linux)")
    print('       set SKIP_VALIDATION=1 && git commit  (Windows CMD)')
    print()
    print("     To revert to default hooks:")
    print("       git config --unset core.hooksPath")

    return 0


if __name__ == "__main__":
    sys.exit(main())
