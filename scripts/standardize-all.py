#!/usr/bin/env python3
"""
Standardize all KSkills packages.

For each skill directory, this script:
  1. Adds `package:` metadata to SKILL.md frontmatter
  2. Creates CHANGELOG.md with initial version entry
  3. Creates install.sh / uninstall.sh for skills with executable code

Usage:
    python3 scripts/standardize-all.py              # apply changes
    python3 scripts/standardize-all.py --dry-run    # preview only
"""

import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ["coding", "stock", "common", "media", "research", "office"]
DRY_RUN = "--dry-run" in sys.argv or "--dry" in sys.argv


def find_skills():
    """Return list of (category, name, path) for all SKILL.md files."""
    result = []
    for cat in CATEGORIES:
        d = ROOT / cat
        if not d.is_dir():
            continue
        for name in sorted(os.listdir(d)):
            skill_dir = d / name
            skill_md = skill_dir / "SKILL.md"
            if skill_dir.is_dir() and skill_md.exists():
                result.append((cat, name, skill_dir))
    return result


def parse_skill(path):
    """Return (frontmatter_lines, body_text) or raise."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        raise ValueError("no frontmatter")
    return m.group(1).split("\n"), text[m.end():]


def write_skill(path, fm, body):
    content = "---\n" + "\n".join(fm) + "\n---" + body
    if not DRY_RUN:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def get_version(fm):
    for line in fm:
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return "1.0.0"


def classify(cat, skill_dir):
    """Return: 'node' | 'python' | 'knowledge-only'"""
    scripts_dir = skill_dir / "scripts"
    # 根目录脚本（无 scripts/ 子目录，如 selection-strategies 的 run_*.py）
    root_py = any(f.suffix == ".py" and f.is_file() for f in skill_dir.iterdir())
    root_js = any(f.suffix == ".js" and f.is_file() for f in skill_dir.iterdir())
    if not scripts_dir.is_dir() and not root_py and not root_js:
        return "knowledge-only"
    if (skill_dir / "package.json").exists() or root_js:
        return "node"
    return "python"


def guess_entry(pkg_type, skill_dir):
    """Guess the entry point script path."""
    if pkg_type == "knowledge-only":
        return None
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return None
    # Prefer __main__.py or cli.py, then any .py/.js file
    for preferred in ["__main__.py", "cli.py", "main.py", "generate.py",
                       "index.js", "generate.js", "cli.js"]:
        if (scripts_dir / preferred).exists():
            return f"scripts/{preferred}"
    # Fallback: first .py or .js file
    for f in sorted(scripts_dir.iterdir()):
        if f.suffix in (".py", ".js") and f.is_file():
            return f"scripts/{f.name}"
    # 根目录脚本（无 scripts/ 子目录）：取首个 .py/.js 文件
    for f in sorted(skill_dir.iterdir()):
        if f.suffix in (".py", ".js") and f.is_file():
            return f.name
    return None


def file_exists(path):
    return path.exists() or (DRY_RUN and not path.parent.name.startswith("."))


# ── Step 1: Add package: block ──────────────────────────────────────────

def add_package(fm_lines, pkg_type, entry):
    """Add `package:` block into frontmatter. Returns new lines (or same if already present)."""
    # Already present?
    for line in fm_lines:
        if line.strip() == "package:":
            return fm_lines  # leave as-is

    # Build package block
    pkg = ["", "package:"]
    pkg.append(f"  type: {pkg_type}")
    if entry:
        pkg.append(f"  entry: {entry}")

    # Insert: after the last "simple" field before capabilities/metadata/requires/inputs
    simple_end = len(fm_lines)
    for i in range(len(fm_lines) - 1, -1, -1):
        line = fm_lines[i]
        if any(line.startswith(k) for k in ("tags:", "category:", "keywords:", "dependencies:")):
            # Skip any indented continuation lines
            j = i + 1
            while j < len(fm_lines) and (fm_lines[j].startswith("  ") or fm_lines[j].startswith("- ") or fm_lines[j].strip() == ""):
                j += 1
            simple_end = j
            break
    if simple_end == len(fm_lines):
        for i, line in enumerate(fm_lines):
            if any(line.startswith(k) for k in ("capabilities:", "metadata:", "requires:", "inputs:")):
                simple_end = i
                break

    return fm_lines[:simple_end] + pkg + fm_lines[simple_end:]


# ── Step 2: Create CHANGELOG.md ─────────────────────────────────────────

def ensure_changelog(skill_dir, version):
    path = skill_dir / "CHANGELOG.md"
    if path.exists():
        return False
    content = f"""# Changelog

## [{version}] - {date.today().isoformat()}

### Added
- Initial standardized package structure.
"""
    if not DRY_RUN:
        path.write_text(content, encoding="utf-8")
    return True


# ── Step 3: Create install.sh ───────────────────────────────────────────

def ensure_install(skill_dir, pkg_type, name):
    path = skill_dir / "install.sh"
    if path.exists():
        return False

    if pkg_type == "node":
        content = """#!/bin/sh
# Install script for {name}
set -e

echo "→ Installing {name}..."

# Check Node.js
if ! command -v node > /dev/null 2>&1; then
    echo "  ⚠  Node.js is required but not found."
    echo "     Install from: https://nodejs.org/"
    exit 1
fi

# Install npm dependencies
if [ -f package.json ]; then
    npm install
    echo "  → npm dependencies installed"
fi

echo "  ✓  {name} installed successfully."
echo ""
echo "  Usage:"
echo "    node scripts/..." 
""".format(name=name)
    else:
        content = """#!/bin/sh
# Install script for {name}
set -e

echo "→ Installing {name}..."

# Check Python
if ! command -v python3 > /dev/null 2>&1; then
    echo "  ⚠  Python 3 is required but not found."
    exit 1
fi

# Install Python dependencies
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
    echo "  → Python dependencies installed"
fi

echo "  ✓  {name} installed successfully."
echo ""
echo "  Environment variables needed:"
echo "    See SKILL.md frontmatter for details."
""".format(name=name)

    if not DRY_RUN:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)
    return True


# ── Step 4: Create uninstall.sh ─────────────────────────────────────────

def ensure_uninstall(skill_dir, pkg_type, name):
    path = skill_dir / "uninstall.sh"
    if path.exists():
        return False

    content = """#!/bin/sh
# Uninstall script for {name}
set -e

echo "→ Uninstalling {name}..."

if [ -f package.json ]; then
    rm -rf node_modules 2>/dev/null || true
    echo "  → Removed node_modules"
fi

echo "  ✓  {name} uninstalled successfully."
""".format(name=name)

    if not DRY_RUN:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)
    return True


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    skills = find_skills()
    counts = {"pkg": 0, "changelog": 0, "install": 0, "uninstall": 0}
    types = {"knowledge-only": 0, "python": 0, "node": 0}

    print(f"{'='*70}")
    print(f" KSkills Standardization")
    print(f"{'='*70}")
    if DRY_RUN:
        print(" [DRY RUN — no changes will be made]\n")

    for cat, name, skill_dir in skills:
        skill_md = skill_dir / "SKILL.md"
        try:
            fm, body = parse_skill(skill_md)
        except ValueError as e:
            print(f"  ⚠  {cat}/{name}: {e}")
            continue

        pkg_type = classify(cat, skill_dir)
        entry = guess_entry(pkg_type, skill_dir)
        version = get_version(fm)
        types[pkg_type] += 1

        changed = False

        # 1. Add package block
        new_fm = add_package(fm, pkg_type, entry)
        if new_fm != fm:
            counts["pkg"] += 1
            changed = True
            write_skill(skill_md, new_fm, body)
            fm = new_fm

        # 2. CHANGELOG.md
        if ensure_changelog(skill_dir, version):
            counts["changelog"] += 1

        # 3. install.sh (only for code skills)
        if pkg_type != "knowledge-only":
            if ensure_install(skill_dir, pkg_type, name):
                counts["install"] += 1

        # 4. uninstall.sh (only for code skills)
        if pkg_type != "knowledge-only":
            if ensure_uninstall(skill_dir, pkg_type, name):
                counts["uninstall"] += 1

        icon = {"knowledge-only": "📖", "python": "🐍", "node": "🟢"}.get(pkg_type, "📦")
        entry_str = f" entry={entry}" if entry else ""
        print(f"  {icon} {cat:<10} {name:<35}  {pkg_type:<15} v{version}{entry_str}")

    print(f"\n{'='*70}")
    print(f" Summary")
    print(f"{'='*70}")
    print(f"  Skills scanned          : {len(skills)}")
    print(f"  package: field added    : {counts['pkg']}")
    print(f"  CHANGELOG.md created    : {counts['changelog']}")
    print(f"  install.sh created      : {counts['install']}")
    print(f"  uninstall.sh created    : {counts['uninstall']}")
    print(f"\n  Breakdown by type:")
    print(f"    knowledge-only : {types['knowledge-only']}")
    print(f"    python         : {types['python']}")
    print(f"    node           : {types['node']}")

    if DRY_RUN:
        print("\n  [DRY RUN] Run without --dry to apply changes.")


if __name__ == "__main__":
    main()
