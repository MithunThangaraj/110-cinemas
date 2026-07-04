---
name: code-review-expert
description: Use when reviewing code in this project. Provides structured, constructive feedback focused on correctness, Django conventions, test coverage, and maintainability.
---

# Code Review Expert

When reviewing code in this project, check the following areas in order.

## Correctness

- Does the logic do what it's supposed to do?
- Are there edge cases that aren't handled (empty querysets, None values, concurrent requests)?
- For seat reservations: is there a race condition risk? Should a `select_for_update()` lock be used?

## Django conventions

- Is ORM usage efficient? Watch for N+1 queries — suggest `select_related` / `prefetch_related`.
- Are URL names used instead of hardcoded paths?
- Are migrations present for any model changes?
- Is `request.htmx` checked before returning partials?

## Code quality

- Are views thin? If a view contains more than ~20 lines of logic, suggest extracting to a service.
- Are there magic strings or numbers that should be constants?
- Is there dead code or unused imports?
- Does it pass `pylint` and `black`? Flag anything that obviously wouldn't.

## Tests

- Are there tests for the changed behavior?
- Are happy path and at least one failure/edge case covered?
- Are HTMX views tested with the `HX-Request` header?

## Security

- Is user input validated through a form or serializer before use?
- Is there any raw SQL? Flag it.
- Are views that require login protected with `@login_required` or `LoginRequiredMixin`?

## Feedback format

- Group feedback by severity: **must fix**, **should fix**, **suggestion**.
- Be specific — point to the exact line or pattern, and explain why it matters.
- Always suggest a concrete fix, not just a problem description.
- Do not make changes directly when in review mode — only suggest.
