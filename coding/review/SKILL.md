---
name: Code Review
description: "Review uncommitted or branch changes and report findings by severity with file:line references."

package:
  type: knowledge-only
---
# Code Review Skill

Inspect the requested changes (uncommitted, a branch, or a commit) and report findings.

Group findings by severity:

- **Critical** — bugs, data loss, security issues, broken builds. Must fix.
- **Important** — likely bugs, maintainability, missing tests. Should fix.
- **Minor** — style, naming, nitpicks. Optional.

Each finding includes a `file:line` reference and a concrete suggested fix. Confirm the issue exists before reporting it.
