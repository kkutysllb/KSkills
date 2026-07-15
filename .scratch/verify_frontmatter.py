#!/usr/bin/env python3
"""
独立审计 14 个 SKILL.md 的 rich frontmatter。
对照 .val.out 缓存，输出每文件实际拥有的 top-level 字段及缺失清单。

Usage:
    python3 .scratch/verify_frontmatter.py
    python3 .scratch/verify_frontmatter.py --json
    python3 .scratch/verify_frontmatter.py --out frontmatter.report.txt
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

# 9 个 rich frontmatter 必需字段
REQUIRED_FIELDS = {
    "name", "version", "author", "license",
    "capabilities", "permissions", "metadata", "tags", "category",
}

# 14 个 .val.out 报失败的文件（rel path from repo root）
SKILLS = [
    "stock/a-stock-screener/SKILL.md",
    "stock/kk-cb-analysis/SKILL.md",
    "stock/kk-news-search/SKILL.md",
    "stock/kk-business-query/SKILL.md",
    "stock/kk-market-linkage-engine/SKILL.md",
    "stock/kk-earnings-forecast/SKILL.md",
    "stock/kk-earnings-revision/SKILL.md",
    "stock/kk-event-query/SKILL.md",
    "stock/kk-financial-statement/SKILL.md",
    "stock/kk-macro-query/SKILL.md",
    "stock/kk-mcf/SKILL.md",
    "stock/kk-report-search/SKILL.md",
    "stock/kk-valuation-model/SKILL.md",
    "stock/kk-zhishu-query/SKILL.md",
]


def extract_frontmatter(text: str) -> tuple[str | None, int]:
    """返回 (yaml_text, end_offset)。失败返回 (None, -1)。"""
    if not text.startswith("---"):
        return None, -1
    m = re.search(r"\n---\s*\n", text[3:])
    if not m:
        return None, -1
    end = 3 + m.start() + 1  # 第二个 --- 起始位置
    return text[3:end].strip("\n"), end


def top_level_keys(yaml_text: str) -> list[str]:
    """提取顶层 key。YAML 解析失败时回退到行首 - 字母下划线 启发式。"""
    keys: list[str] = []
    for line in yaml_text.splitlines():
        if re.match(r"^[A-Za-z_][\w-]*\s*:", line):
            keys.append(line.split(":", 1)[0].strip())
    # 去重保序
    seen, out = set(), []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def audit(repo_root: Path) -> dict:
    report = []
    for rel in SKILLS:
        p = repo_root / rel
        if not p.exists():
            report.append({
                "file": rel,
                "exists": False,
                "keys": [],
                "missing": list(REQUIRED_FIELDS),
                "status": "MISSING_FILE",
            })
            continue
        text = p.read_text(encoding="utf-8")
        fm, _ = extract_frontmatter(text)
        if fm is None:
            report.append({
                "file": rel,
                "exists": True,
                "keys": [],
                "missing": list(REQUIRED_FIELDS),
                "status": "NO_FRONTMATTER",
            })
            continue
        keys = top_level_keys(fm)
        missing = [k for k in REQUIRED_FIELDS if k not in keys]
        status = "PASS" if not missing else f"MISSING({len(missing)})"
        report.append({
            "file": rel,
            "exists": True,
            "keys": keys,
            "missing": missing,
            "status": status,
        })
    return {
        "repo_root": str(repo_root),
        "required_fields": sorted(REQUIRED_FIELDS),
        "skills": report,
        "summary": {
            "total": len(report),
            "pass": sum(1 for r in report if r["status"] == "PASS"),
            "fail": sum(1 for r in report if r["status"] != "PASS" and r["file"].endswith("SKILL.md")),
        },
    }


def render_text(report: dict) -> str:
    lines = [
        "=" * 70,
        "FRONTMATTER AUDIT — 14 skills",
        f"Repo: {report['repo_root']}",
        f"Required fields: {', '.join(report['required_fields'])}",
        "=" * 70,
    ]
    for r in report["skills"]:
        flag = "✅" if r["status"] == "PASS" else "❌"
        keys_short = ", ".join(r["keys"])
        lines.append(f"{flag} {r['file']:50s}  [{r['status']}]")
        lines.append(f"   keys({len(r['keys'])}): {keys_short}")
        if r["missing"]:
            lines.append(f"   MISSING: {', '.join(r['missing'])}")
    s = report["summary"]
    lines += [
        "=" * 70,
        f"SUMMARY: {s['pass']}/{s['total']} pass, {s['fail']} fail",
        "=" * 70,
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", help="repo root (default: cwd)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", help="write report to this file")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    report = audit(repo)
    if args.json:
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(payload, encoding="utf-8")
        else:
            print(payload)
    else:
        text = render_text(report)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
    # exit code: 0 if all pass, 1 otherwise
    return 0 if report["summary"]["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
