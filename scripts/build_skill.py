#!/usr/bin/env python3
"""
Skill Packager — 打包技能目录为 .skill 压缩包

支持三种打包范围：
  1. 单个技能   : python3 scripts/build_skill.py stock/business-query
  2. 类别目录   : python3 scripts/build_skill.py stock          # 打包 stock/ 下所有技能
  3. 全仓库     : python3 scripts/build_skill.py --all

Usage:
    python3 scripts/build_skill.py <skill-dir | category-dir>
    python3 scripts/build_skill.py <skill-dir> -o ./releases
    python3 scripts/build_skill.py stock -o ./releases          # 类别目录批量打包
    python3 scripts/build_skill.py --all
    python3 scripts/build_skill.py <skill-dir> --no-validate
    python3 scripts/build_skill.py <skill-dir> --no-manifest

智能识别规则（传入位置参数时）：
  - 目录直接含 SKILL.md         → 视为单个技能目录，打包之
  - 目录不含 SKILL.md 但子目录有 → 视为类别目录，批量打包其下所有技能
  - 两者皆无                    → 报错退出

Examples:
    python3 scripts/build_skill.py stock/business-query
    python3 scripts/build_skill.py coding/test-driven-development -o ./dist
    python3 scripts/build_skill.py stock                        # 打包 stock 下所有技能
    python3 scripts/build_skill.py media research               # 同时打包多个类别（未来扩展）
    python3 scripts/build_skill.py --all

输出: <output-dir>/<name>-<version>.skill （zip 格式，扩展名 .skill）
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Optional

# 复用仓库现有的 frontmatter 解析逻辑
sys.path.insert(0, str(Path(__file__).parent))
from validate_skills import parse_frontmatter, validate_file, SEV_ERROR  # noqa: E402

# ── 排除规则 ──────────────────────────────────────────────────────────────────
# 参考 skill-creator 的 package_skill.py + 本仓库实际污染情况。

# 始终排除（任意层级）：构建产物、IDE/OS 缓存、临时文件
EXCLUDE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    "__MACOSX",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".eggs",
    "*.egg-info",
    "dist",
    "build",
}
EXCLUDE_GLOBS = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    ".DS_Store?",
    "._*",
    "*.swp",
    "*.swo",
    "*~",
    "Thumbs.db",
    "ehthumbs.db",
}
# 仅在技能根目录排除（保留嵌套同名目录）：开发期工件
ROOT_EXCLUDE_DIRS = {"evals", "*-workspace"}


def should_exclude(rel_path: Path) -> bool:
    """判断相对路径是否应被排除出打包。"""
    parts = rel_path.parts
    # 1. 任意层级的目录排除
    for part in parts:
        if part in EXCLUDE_DIRS or any(fnmatch.fnmatch(part, pat) for pat in EXCLUDE_DIRS):
            return True
    # 2. 仅根目录排除：rel_path 相对于技能目录，parts[0] 是技能根下第一级
    if len(parts) > 1:
        first = parts[0]
        for pat in ROOT_EXCLUDE_DIRS:
            if fnmatch.fnmatch(first, pat):
                return True
    # 3. 文件名 glob 排除
    name = rel_path.name
    for pat in EXCLUDE_GLOBS:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


# ── 元数据提取 ────────────────────────────────────────────────────────────────

KSKILLS_VERSION = "1.0.0"


def extract_meta(skill_path: Path) -> dict:
    """从 SKILL.md 提取打包所需的元数据。"""
    skill_md = skill_path / "SKILL.md"
    data, _raw, err = parse_frontmatter(skill_md)
    if err or data is None:
        return {}

    pkg = data.get("package") or {}
    pkg_type = pkg.get("type", "knowledge-only") if isinstance(pkg, dict) else "knowledge-only"
    # 统一标记：未声明 package.type 的也视作 knowledge-only
    if not pkg_type:
        pkg_type = "knowledge-only"

    requires = data.get("requires") or {}
    perms = data.get("permissions") or {}

    return {
        "name": data.get("name") or skill_path.name,
        "version": str(data.get("version") or "0.0.0"),
        "category": data.get("category") or _guess_category(skill_path),
        "author": data.get("author") or "",
        "license": data.get("license") or "",
        "description": data.get("description") or "",
        "package_type": pkg_type,
        "entry": pkg.get("entry") if isinstance(pkg, dict) else None,
        "requires": {
            "bins": requires.get("bins", []) if isinstance(requires, dict) else [],
            "packages": requires.get("packages", []) if isinstance(requires, dict) else [],
            "env": perms.get("env", []) if isinstance(perms, dict) and perms.get("env") else [],
        },
    }


def _guess_category(skill_path: Path) -> str:
    """从路径推断类别：仓库根/category/skill-name/SKILL.md"""
    try:
        # skill_path 是 .../KSkills/<category>/<skill-name>
        parts = skill_path.resolve().parts
        # 找到 KSkills 后面的第一个目录
        if "KSkills" in parts:
            idx = parts.index("KSkills")
            return parts[idx + 1] if idx + 1 < len(parts) else "unknown"
    except Exception:
        pass
    return skill_path.parent.name if skill_path.parent.name else "unknown"


# ── 校验 ──────────────────────────────────────────────────────────────────────


def run_validation(skill_path: Path) -> tuple[bool, list[str]]:
    """调用 validate_skills.validate_file 校验单个技能。"""
    skill_md = skill_path / "SKILL.md"
    findings = validate_file(str(skill_md))
    errors = [msg for sev, msg in findings if sev == SEV_ERROR]
    return (len(errors) == 0), errors


# ── 清单生成 ──────────────────────────────────────────────────────────────────


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(skill_path: Path, meta: dict, file_entries: list[dict]) -> dict:
    """生成 SKILL-MANIFEST.json 内容。"""
    return {
        "name": meta["name"],
        "version": meta["version"],
        "category": meta["category"],
        "package_type": meta["package_type"],
        "entry": meta["entry"],
        "author": meta["author"],
        "license": meta["license"],
        "description": meta["description"],
        "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "kskills_version": KSKILLS_VERSION,
        "requires": meta["requires"],
        "files": file_entries,
    }


# ── 打包 ──────────────────────────────────────────────────────────────────────


def package_one(skill_path: Path, output_dir: Path, *, validate: bool, manifest: bool) -> Optional[Path]:
    """打包单个技能目录，返回生成的 .skill 文件路径。"""
    skill_path = skill_path.resolve()
    if not skill_path.is_dir():
        print(f"❌ 不是目录: {skill_path}")
        return None

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ 缺少 SKILL.md: {skill_path}")
        return None

    meta = extract_meta(skill_path)
    name = meta["name"]
    version = meta["version"]

    # 校验
    if validate:
        print(f"🔍 校验 {name} ...")
        ok, errors = run_validation(skill_path)
        if not ok:
            print(f"❌ 校验失败，拒绝打包：")
            for e in errors:
                print(f"   • {e}")
            print("   提示：使用 --no-validate 可跳过（不推荐）。")
            return None
        print(f"✅ 校验通过\n")

    # 输出路径
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{name}-{version}.skill"

    print(f"📦 打包 {name} v{version} → {out_file}")

    file_entries = []
    added = 0
    skipped = 0

    try:
        with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for fp in skill_path.rglob("*"):
                if not fp.is_file():
                    continue
                # arcname 以技能目录名为根，便于解压后定位
                arcname = fp.relative_to(skill_path.parent)
                rel_for_check = fp.relative_to(skill_path)
                if should_exclude(rel_for_check):
                    skipped += 1
                    continue
                data = fp.read_bytes()
                zipf.writestr(str(arcname), data)
                file_entries.append({
                    "path": str(arcname),
                    "sha256": sha256_of(data),
                    "size": len(data),
                })
                added += 1

            # 注入 manifest
            if manifest:
                man = build_manifest(skill_path, meta, file_entries)
                manifest_arc = f"{skill_path.name}/SKILL-MANIFEST.json"
                zipf.writestr(manifest_arc, json.dumps(man, indent=2, ensure_ascii=False))
                print(f"  ✓ 注入清单 {manifest_arc}")

    except Exception as e:
        print(f"❌ 打包失败: {e}")
        if out_file.exists():
            out_file.unlink()
        return None

    size_kb = out_file.stat().st_size / 1024
    print(f"✅ 完成：{out_file}  ({added} 文件, 排除 {skipped}, {size_kb:.1f} KB)")
    return out_file


def discover_skills(root: Path) -> list[Path]:
    """递归扫描 root 下所有含 SKILL.md 的技能目录（去重并排序）。

    过滤规则：跳过 .git / dist / 顶级输出目录，避免把构建产物当技能。
    """
    # root 可能是仓库根、类别目录（stock/）、或子类别目录
    # 相对 root 的路径片段用于过滤；.git / dist 在任意层级都跳过
    skills = []
    seen = set()
    for p in root.rglob("SKILL.md"):
        # 用 resolve 后的路径去重，避免符号链接导致重复
        parent = p.parent.resolve()
        if parent in seen:
            continue
        # 过滤：路径中任一片段命中即跳过
        if any(part in {".git", "dist", "build"} for part in p.parts):
            continue
        seen.add(parent)
        skills.append(p.parent)
    return sorted(skills)


def package_all(root: Path, output_dir: Path, *, validate: bool, manifest: bool,
                scope_label: Optional[str] = None) -> list[Path]:
    """批量打包 root 下所有技能（含 SKILL.md 的目录）。

    Args:
        root: 扫描根（仓库根 或 类别目录）
        scope_label: 显示用的人类可读范围描述，默认取 root 目录名
    """
    skills = discover_skills(root)
    label = scope_label or root.name or str(root)
    print(f"📂 扫描范围：{label}")
    print(f"   发现 {len(skills)} 个技能\n")
    if not skills:
        print(f"⚠️  {root} 下未发现任何 SKILL.md，无可打包内容。")
        return []
    results = []
    failed = []
    for sp in skills:
        print(f"{'─' * 60}")
        res = package_one(sp, output_dir, validate=validate, manifest=manifest)
        if res:
            results.append(res)
        else:
            failed.append(sp.name)
        print()

    print(f"{'=' * 60}")
    print(f"  打包完成：成功 {len(results)} / 失败 {len(failed)}")
    if failed:
        print(f"  失败列表：{', '.join(failed)}")
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="build_skill.py",
        description="把技能目录打包成 .skill 压缩包（支持单技能 / 类别目录批量 / 全仓库）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  # 单个技能
  python3 scripts/build_skill.py stock/business-query
  python3 scripts/build_skill.py coding/test-driven-development -o ./releases

  # 类别目录下所有技能（自动识别）
  python3 scripts/build_skill.py stock              # 打包 stock/ 下全部技能
  python3 scripts/build_skill.py coding -o ./dist   # 打包 coding/ 下全部技能
  python3 scripts/build_skill.py media research     # 同时打包多个类别目录

  # 全仓库
  python3 scripts/build_skill.py --all
""",
    )
    ap.add_argument("paths", nargs="*", help="技能目录或类别目录路径（如 stock/foo 或 stock）；可传多个")
    ap.add_argument("-o", "--output", default="dist", help="输出目录（默认 dist/）")
    ap.add_argument("--all", action="store_true", help="打包仓库内所有技能")
    ap.add_argument("--no-validate", action="store_true", help="跳过 frontmatter 校验")
    ap.add_argument("--no-manifest", action="store_true", help="不注入 SKILL-MANIFEST.json")
    args = ap.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output).resolve()

    if args.all:
        if args.paths:
            ap.error("--all 不能与位置参数同时使用")
        package_all(repo_root, output_dir, validate=not args.no_validate,
                    manifest=not args.no_manifest, scope_label="全仓库")
        return 0

    if not args.paths:
        ap.print_help()
        return 1

    # 解析每个位置参数：可能是相对路径或绝对路径
    resolved_paths: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        if not p.is_absolute():
            cand = repo_root / raw
            p = cand if cand.exists() else Path(raw)
        if not p.exists():
            print(f"❌ 路径不存在: {raw}")
            return 1
        resolved_paths.append(p.resolve())

    # 分类处理：单技能 / 类别目录
    single_skills: list[Path] = []
    category_dirs: list[Path] = []
    for p in resolved_paths:
        if (p / "SKILL.md").exists():
            single_skills.append(p)
        elif any(True for _ in p.rglob("SKILL.md")):
            category_dirs.append(p)
        else:
            print(f"❌ 未发现 SKILL.md（既不是技能目录，也不是类别目录）: {p}")
            return 1

    exit_code = 0
    total_ok = 0
    total_fail = 0

    # 1) 单技能：逐个打包
    for sp in single_skills:
        print(f"{'─' * 60}")
        res = package_one(sp, output_dir, validate=not args.no_validate, manifest=not args.no_manifest)
        if res:
            total_ok += 1
        else:
            total_fail += 1
            exit_code = 1
        print()

    # 2) 类别目录：批量打包
    for cat in category_dirs:
        print("═" * 60)
        results = package_all(cat, output_dir, validate=not args.no_validate,
                              manifest=not args.no_manifest,
                              scope_label=f"类别目录 {cat.name}/")
        total_ok += len(results)
        # package_all 内部已统计失败，这里仅以「期望 vs 实际」粗略推断
        expected = len(discover_skills(cat))
        total_fail += max(0, expected - len(results))
        if expected > len(results):
            exit_code = 1
        print()

    # 多目标汇总
    if len(resolved_paths) > 1 or category_dirs:
        print("═" * 60)
        print(f"  汇总：成功 {total_ok} / 失败 {total_fail}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
