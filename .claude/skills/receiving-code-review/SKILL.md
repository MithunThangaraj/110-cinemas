---
name: receiving-code-review
description: Use when responding to code review feedback on this project. Helps process review comments, decide what to act on, and implement changes cleanly.
---

# Receiving Code Review

When review feedback has been given, work through it systematically.

## Processing feedback

1. Read all comments before making any changes.
2. Group by: **must fix** → **should fix** → **suggestion / optional**.
3. For anything unclear, ask one clarifying question before implementing.

## Implementing changes

- Address **must fix** items first, one at a time.
- After each fix, re-run `uv run pytest --cov` to confirm nothing broke.
- Run `uv run black .` and `uv run pylint cinema` after all changes.
- Keep each fix in a logical commit if committing incrementally.

## When to push back

- If a suggestion contradicts existing project conventions in `AGENTS.md`, note the conflict and ask which takes priority.
- If a refactor is too broad relative to the PR scope, acknowledge it but suggest it as a separate task.
- If you disagree with feedback, explain why with a concrete reason — don't just ignore it.

## After review

- Respond to each comment (even if just "done" or "addressed in <commit>").
- If a comment led to a broader insight, consider updating `openspec/specs/` to capture it.
