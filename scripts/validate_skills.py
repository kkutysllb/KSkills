#!/usr/bin/env python3
"""
SKILL.md frontmatter schema validator.

Two schema profiles are auto-detected by category:
  - "minimal" (coding/, research/, media/):  name + description (+ optional license)
  - "rich"    (stock/, common/):             name + description + version + author +
                                            license + capabilities + permissions +
                                            metadata + tags (+ optional requires, inputs)

Exit code: 0 if no errors, 1 if any ERROR-level findings.
"""

import os
import re
import sys
from collections import defaultdict

try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML is required. Install with: pip3 install pyyaml")

# ── Schema definition ────────────────────────────────────────────────────────

RICH_CATEGORIES = {"stock", "common"}

RICH_REQUIRED = ["name", "description", "version", "author", "license",
                 "capabilities", "permissions", "metadata", "tags"]

RICH_OPTIONAL = ["requires", "inputs", "category"]

MINIMAL_REQUIRED = ["name", "description"]
MINIMAL_OPTIONAL = ["license", "version", "author"]

KNOWN_KEYS = set(RICH_REQUIRED + RICH_OPTIONAL + MINIMAL_REQUIRED + MINIMAL_OPTIONAL + ["dependencies", "keywords"])

# ── Severity ─────────────────────────────────────────────────────────────────

SEV_ERROR = "ERROR"
SEV_WARN  = "WARN "
SEV_INFO  = "INFO "


def collect_files(root="."):
    """Find all SKILL.md files, return sorted list of paths."""
    result = []
    for dirpath, _, files in os.walk(root):
        if "SKILL.md" in files:
            result.append(os.path.join(dirpath, "SKILL.md"))
    return sorted(result)


def parse_frontmatter(path):
    """Return (data dict or None, raw frontmatter str or None, error or None)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, None, "no YAML frontmatter block found"
    raw = m.group(1)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return None, raw, f"YAML parse error: {e}"
    if not isinstance(data, dict):
        return None, raw, "frontmatter is not a mapping"
    return data, raw, None


def validate_file(path):
    """Return list of (severity, message) findings for a single file."""
    findings = []
    data, raw, err = parse_frontmatter(path)
    if err:
        findings.append((SEV_ERROR, err))
        return findings

    # Determine category from path: ./category/skill/SKILL.md
    parts = path.replace("\\", "/").split("/")
    category = parts[1] if len(parts) >= 3 else "root"
    is_rich = category in RICH_CATEGORIES
    profile = "rich" if is_rich else "minimal"

    # ── Required fields ──────────────────────────────────────────────────────
    required = RICH_REQUIRED if is_rich else MINIMAL_REQUIRED
    optional = RICH_OPTIONAL if is_rich else MINIMAL_OPTIONAL

    for field in required:
        if field not in data:
            findings.append((SEV_ERROR, f"[{profile}] missing required field '{field}'"))

    # ── Unknown fields ───────────────────────────────────────────────────────
    for key in data:
        if key not in KNOWN_KEYS:
            findings.append((SEV_WARN, f"unknown field '{key}' (not in known schema)"))

    # ── Field-level type / value checks ──────────────────────────────────────

    name = data.get("name")
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            findings.append((SEV_ERROR, "field 'name' must be a non-empty string"))
        else:
            # dir name should match skill name (with or without kk- prefix)
            dir_name = os.path.basename(os.path.dirname(path))
            base_name = name
            # allow kk- prefix mismatch for media/ stock dirs
            candidates = {dir_name, dir_name.removeprefix("kk-")}
            if name not in candidates and dir_name not in {name, f"kk-{name}"}:
                findings.append((SEV_WARN,
                    f"dir name '{dir_name}' does not match skill name '{name}'"))

    desc = data.get("description")
    if desc is not None:
        if not isinstance(desc, str) or len(desc.strip()) < 10:
            findings.append((SEV_ERROR,
                f"field 'description' too short or empty ({len(str(desc))} chars, need >= 10)"))

    version = data.get("version")
    if version is not None:
        vs = str(version)
        if not re.match(r"^\d+\.\d+", vs):
            findings.append((SEV_WARN, f"field 'version'='{vs}' is not semver-like (X.Y or X.Y.Z)"))

    # ── Rich-only structural checks ──────────────────────────────────────────
    if is_rich:
        caps = data.get("capabilities")
        if caps is not None:
            if not isinstance(caps, list) or len(caps) == 0:
                findings.append((SEV_ERROR, "'capabilities' must be a non-empty list"))
            else:
                for i, cap in enumerate(caps):
                    if not isinstance(cap, dict) or "id" not in cap or "description" not in cap:
                        findings.append((SEV_ERROR,
                            f"'capabilities[{i}]' must have 'id' and 'description'"))

        perms = data.get("permissions")
        if perms is not None:
            if not isinstance(perms, dict):
                findings.append((SEV_ERROR, "'permissions' must be a mapping"))
            else:
                for pk in ("network", "filesystem", "shell"):
                    if pk in perms and not isinstance(perms[pk], bool):
                        findings.append((SEV_WARN,
                            f"'permissions.{pk}' should be boolean, got {type(perms[pk]).__name__}"))
                if "env" in perms and perms["env"] is not None:
                    if not isinstance(perms["env"], list):
                        findings.append((SEV_WARN, "'permissions.env' should be a list"))

        meta = data.get("metadata")
        if meta is not None and isinstance(meta, dict):
            oc = meta.get("openclaw")
            if oc is not None and isinstance(oc, dict):
                # version consistency
                oc_ver = oc.get("version")
                if version is not None and str(oc_ver) != str(version):
                    findings.append((SEV_WARN,
                        f"version mismatch: top-level={version} vs metadata.openclaw.version={oc_ver}"))
                # author consistency
                oc_author = oc.get("author")
                author = data.get("author")
                if author is not None and oc_author is not None and str(oc_author) != str(author):
                    findings.append((SEV_WARN,
                        f"author mismatch: top-level={author} vs metadata.openclaw.author={oc_author}"))
                # tags consistency
                oc_tags = oc.get("tags")
                top_tags = data.get("tags")
                if isinstance(top_tags, list) and isinstance(oc_tags, list):
                    if sorted(top_tags) != sorted(oc_tags):
                        findings.append((SEV_WARN,
                            f"tags mismatch: top={sorted(top_tags)} vs openclaw={sorted(oc_tags)}"))

        tags = data.get("tags")
        if tags is not None:
            if not isinstance(tags, list) or len(tags) == 0:
                findings.append((SEV_ERROR, "'tags' must be a non-empty list"))

        reqs = data.get("requires")
        if reqs is not None:
            if not isinstance(reqs, dict):
                findings.append((SEV_WARN, "'requires' should be a mapping"))

        inputs = data.get("inputs")
        if inputs is not None:
            if not isinstance(inputs, list):
                findings.append((SEV_WARN, "'inputs' should be a list"))

    # ── Optional-but-recommended fields for rich profile ─────────────────────
    if is_rich:
        for field in RICH_OPTIONAL:
            if field not in data:
                # requires/inputs/category are common but not strictly required
                if field == "category":
                    findings.append((SEV_INFO, f"recommended field '{field}' is missing"))

    return findings


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    files = collect_files(root)
    if not files:
        print("No SKILL.md files found.")
        return 0

    total_errors = 0
    total_warns  = 0
    total_infos  = 0
    clean_count  = 0

    # Group by category for summary
    cat_stats = defaultdict(lambda: {"files": 0, "errors": 0, "warns": 0, "infos": 0})

    print(f"{'='*80}")
    print(f" SKILL.md Frontmatter Schema Validator")
    print(f" Scanning {len(files)} files under '{root}'")
    print(f"{'='*80}\n")

    for path in files:
        parts = path.replace("\\", "/").split("/")
        category = parts[1] if len(parts) >= 3 else "root"
        cat_stats[category]["files"] += 1

        findings = validate_file(path)
        if not findings:
            clean_count += 1
            continue

        print(f"── {path} ──")
        for sev, msg in findings:
            icon = {"ERROR": "✗", "WARN ": "▲", "INFO ": "·"}[sev]
            print(f"  {icon} {sev}  {msg}")
            if sev == SEV_ERROR:
                total_errors += 1
                cat_stats[category]["errors"] += 1
            elif sev == SEV_WARN:
                total_warns += 1
                cat_stats[category]["warns"] += 1
            else:
                total_infos += 1
                cat_stats[category]["infos"] += 1
        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"{'='*80}")
    print(f" SUMMARY")
    print(f"{'='*80}")
    print(f"  Total files scanned : {len(files)}")
    print(f"  Clean (no findings) : {clean_count}")
    print(f"  Errors              : {total_errors}")
    print(f"  Warnings            : {total_warns}")
    print(f"  Info                : {total_infos}")
    print()
    print(f"  {'Category':<14} {'Files':>6} {'Errors':>8} {'Warns':>8} {'Info':>8}")
    print(f"  {'-'*14} {'-'*6} {'-'*8} {'-'*8} {'-'*8}")
    for cat in sorted(cat_stats):
        s = cat_stats[cat]
        print(f"  {cat:<14} {s['files']:>6} {s['errors']:>8} {s['warns']:>8} {s['infos']:>8}")
    print()

    if total_errors:
        print(f"✗ FAILED: {total_errors} error(s) found.")
        return 1
    else:
        print(f"✓ PASSED: no schema errors ({total_warns} warning(s), {total_infos} info).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
