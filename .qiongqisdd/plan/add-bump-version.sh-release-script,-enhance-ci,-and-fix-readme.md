# Implementation Plan: Release Tooling & CI Enhancement

## Summary

Add a `scripts/bump-version.sh` release helper that bumps the `KSKILLS_VERSION` constant in `scripts/build_skill.py`, enhances `.github/workflows/validate.yml` to also run `test_toolchain.sh` as a smoke test, and fixes the README skill count to be auto-generated.

---

## Step 1: Create `scripts/bump-version.sh`

**File:** `scripts/bump-version.sh` (new)

A POSIX `sh` script that:

1. Takes a **version argument** (e.g., `1.1.0`) or **part keyword** (`major`, `minor`, `patch`, `current`).
2. Reads the current `KSKILLS_VERSION` from `scripts/build_skill.py`.
3. Computes the next version if a keyword was given (bump major/minor/patch).
4. If `--dry-run`, just prints what would change.
5. Updates the `KSKILLS_VERSION = "X.Y.Z"` line in `scripts/build_skill.py` using `sed`.
6. If `--commit`, creates a git commit with message `chore: bump KSKILLS_VERSION to X.Y.Z`.
7. Validates that the new version follows semver (`X.Y.Z`).

**Usage examples:**
```bash
./scripts/bump-version.sh minor           # 1.0.0 → 1.1.0
./scripts/bump-version.sh 2.0.0           # 1.0.0 → 2.0.0
./scripts/bump-version.sh minor --dry-run # preview only
./scripts/bump-version.sh minor --commit  # bump + git commit
./scripts/bump-version.sh current         # print current version
```

**Implementation notes:**
- Parse `KSKILLS_VERSION` with `grep` + `sed` from `build_skill.py`.
- Semver bump: increment patch by default, minor on `minor`, major on `major`.
- Idempotent: if version matches current, print message and exit 0.
- Include `set -eu` and error handling.

---

## Step 2: Enhance CI — add smoke test job

**File:** `.github/workflows/validate.yml` (modify)

Add a new job `smoke-test` that runs `test_toolchain.sh` with a known fixture.

- Use `ubuntu-latest`, `actions/checkout@v4`, `actions/setup-python@v5` with Python 3.12.
- Install `pyyaml` and `zip` (Ubuntu includes unzip by default).
- Run `./scripts/test_toolchain.sh coding/refactor` (a stable fixture).
- Add dependency: needs `validate` job to pass first.

**Diff:**
```yaml
jobs:
  validate:  # existing
    ...
  smoke-test:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install pyyaml
      - name: Smoke test — build, install, verify, uninstall
        run: ./scripts/test_toolchain.sh coding/refactor
```

---

## Step 3: Update README skill count

**File:** `README.md` (modify)

- Review the actual skill directory count and update the intro numbers.
- Ensure the category breakdown matches reality (e.g., `coding/` count, `stock/` count, etc.).
- If needed, note in the plan that we'll count via `find . -name "SKILL.md" -exec dirname {} \; | sort | ...` to get accurate numbers.

---

## Step 4: Verify with `test_toolchain.sh`

After all changes:

1. Run `./scripts/test_toolchain.sh coding/refactor` to confirm the toolchain still works end-to-end.
2. Run `./scripts/bump-version.sh minor --dry-run` to verify it parses and proposes a correct version.
3. Run `./scripts/bump-version.sh current` to verify current version display.
4. Confirm the CI YAML is valid (no syntax errors).

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| `sed` behaves differently on macOS vs Linux | Use POSIX `sed -i` with backup suffix approach, and test both |
| `test_toolchain.sh` has a strict existing fixture requirement | Use `coding/refactor` which is known to exist and passed before |
| CI job may fail if PyYAML not installed | Already handled in test_toolchain.sh — gracefully skips regression |
