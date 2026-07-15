#!/usr/bin/env python3
"""
Rich-frontmatter gate for stock/ and common/ SKILL.md files.

CI-oriented complement to scripts/validate_skills.py:
  - validate_skills.py: scans ALL SKILL.md files with mixed schema profiles
  - verify_frontmatter.py (this): strict gate on rich-schema skills only

Required top-level fields for a "rich" skill (stock/, common/):
    name, version, author, license,
    capabilities, permissions, metadata, tags, category

Exit codes:
    0  all rich skills have every required field
    1  one or more rich skills are missing required fields
    2  usage / setup error (e.g. PyYAML missing)

Usage:
    python3 scripts/verify_frontmatter.py                # scan repo from cwd
    python3 scripts/verify_frontmatter.py <root>        # scan explicit root
    python3 scripts/verify_frontmatter.py --json         # JSON report on stdout
    python3 scripts/verify_frontmatter.py --strict      # exit 1 on WARN too
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML is required. Install with: pip3 install pyyaml")

# ── Schema definition ────────────────────────────────────────────────────────

REQUIRED_RICH_FIELDS = (
    "name", "version", "author", "license",
    "capabilities", "permissions", "metadata", "tags", "category",
)

RECOMMENDED_RICH_FIELDS = ("description",)

# Categories whose skills must follow the rich schema. Mirrors validate_skills.py.
RICH_CATEGORIES = frozenset({"stock", "common"})

SKILL_FILENAME = "SKILL.md"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

# ── Discovery ────────────────────────────────────────────────────────────────


def find_rich_skill_files(root: Path) -> list[Path]:
    """Walk `root` and return SKILL.md files under rich-schema categories."""
    found: list[Path] = []
    for skill_md in root.rglob(SKILL_FILENAME):
        try:
            rel = skill_md.relative_to(root)
        except ValueError:
            continue
        parts = rel.parts
        if len(parts) >= 2 and parts[0] in RICH_CATEGORIES:
            found.append(skill_md)
    return sorted(found)


# ── Parsing ──────────────────────────────────────────────────────────────────


def parse_frontmatter(path: Path) -> tuple[dict | None, str | None, str | None]:
    """Return (data, raw, error). data is None on any failure."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, None, f"read error: {exc}"

    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, None, "no YAML frontmatter block found"
    raw = m.group(1)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, raw, f"YAML parse error: {exc}"
    if not isinstance(data, dict):
        return None, raw, "frontmatter is not a mapping"
    return data, raw, None


# ── Per-file audit ───────────────────────────────────────────────────────────


def audit_file(path: Path, root: Path) -> dict:
    """Audit one SKILL.md and return a structured result record."""
    rel = str(path.relative_to(root))
    data, _raw, err = parse_frontmatter(path)
    if err:
        return {
            "path": rel,
            "category": path.relative_to(root).parts[0],
            "top_level_keys": [],
            "missing_required": list(REQUIRED_RICH_FIELDS),
            "missing_recommended": list(RECOMMENDED_RICH_FIELDS),
            "errors": [err],
            "warnings": [],
        }

    top_keys = sorted(data.keys())
    present = set(top_keys)
    missing_required = [f for f in REQUIRED_RICH_FIELDS if f not in present]
    missing_recommended = [f for f in RECOMMENDED_RICH_FIELDS if f not in present]

    warnings: list[str] = []
    # Surface quality hints, not just bare presence.
    if "version" in present:
        v = data["version"]
        if not isinstance(v, (str, int, float)) or not re.match(r"^\d+\.\d+", str(v)):
            warnings.append(f"version '{v}' is not semver-like (expected X.Y or X.Y.Z)")

    if "tags" in present:
        tags = data["tags"]
        if not isinstance(tags, list) or len(tags) == 0:
            warnings.append("'tags' must be a non-empty list")

    if "capabilities" in present:
        caps = data["capabilities"]
        if not isinstance(caps, list) or len(caps) == 0:
            warnings.append("'capabilities' must be a non-empty list")

    if "permissions" in present and not isinstance(data["permissions"], dict):
        warnings.append("'permissions' should be a mapping")

    return {
        "path": rel,
        "category": path.relative_to(root).parts[0],
        "top_level_keys": top_keys,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "errors": [],
        "warnings": warnings,
    }


# ── Report rendering ─────────────────────────────────────────────────────────


def render_text(report: dict, root: Path) -> str:
    files = report["files"]
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append(" Rich Frontmatter Gate (stock/ + common/)")
    lines.append(f" Root: {root}")
    lines.append(f" Scanned {len(files)} SKILL.md file(s)")
    lines.append("=" * 80)
    lines.append("")

    for entry in files:
        status = "PASS" if not entry["missing_required"] and not entry["errors"] else "FAIL"
        lines.append(f"[{status}] {entry['path']}")
        lines.append(f"        category : {entry['category']}")
        lines.append(f"        keys     : {', '.join(entry['top_level_keys']) or '(none)'}")

        if entry["missing_required"]:
            lines.append(f"        MISSING  : {', '.join(entry['missing_required'])}")
        if entry["missing_recommended"]:
            lines.append(f"        optional : missing {', '.join(entry['missing_recommended'])}")
        for err in entry["errors"]:
            lines.append(f"        ERROR    : {err}")
        for warn in entry["warnings"]:
            lines.append(f"        WARN     : {warn}")
        lines.append("")

    s = report["summary"]
    lines.append("=" * 80)
    lines.append(" SUMMARY")
    lines.append("=" * 80)
    lines.append(f"  total rich skills : {s['total']}")
    lines.append(f"  passed            : {s['pass']}")
    lines.append(f"  failed            : {s['fail']}")
    lines.append(f"  errors            : {s['errors']}")
    lines.append(f"  warnings          : {s['warnings']}")
    lines.append("")
    if s["fail"] == 0:
        lines.append("OK: every rich-schema SKILL.md has all required fields.")
    else:
        lines.append(f"FAIL: {s['fail']} rich-schema SKILL.md file(s) are missing required fields.")
    return "\n".join(lines) + "\n"


# ── Entry point ──────────────────────────────────────────────────────────────


def audit(root: Path) -> dict:
    files = find_rich_skill_files(root)
    entries = [audit_file(p, root) for p in files]
    summary = {
        "total": len(entries),
        "pass": sum(1 for e in entries if not e["missing_required"] and not e["errors"]),
        "fail": sum(1 for e in entries if e["missing_required"] or e["errors"]),
        "errors": sum(len(e["errors"]) for e in entries),
        "warnings": sum(len(e["warnings"]) for e in entries),
    }
    return {"summary": summary, "files": entries}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", help="repo root to scan (default: cwd)")
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any WARN is present")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR: '{root}' is not a directory", file=sys.stderr)
        return 2

    report = audit(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_text(report, root))

    if report["summary"]["fail"] > 0:
        return 1
    if args.strict and report["summary"]["warnings"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())