---
name: refactor
description: Use when refactoring existing code in this project. Ensures refactors stay safe, targeted, and don't change behavior.
---

# Refactor

Rules for refactoring code in this project.

## Before starting

- Confirm the existing tests pass: `uv run pytest --cov`.
- Note the current test coverage for the area being refactored.
- Understand what the code does before changing how it does it.

## Refactor principles

- **Change structure, not behavior.** A refactor should not change what the code does.
- **One thing at a time.** Don't combine a refactor with a bug fix or new feature in the same change.
- **Small steps.** Refactor incrementally and run tests after each step.
- **Prefer clarity over cleverness.** The next person reading this will thank you.

## Common refactors in this project

**Extract service function**: if a view has complex logic, extract it to `cinema/services.py`.
```python
# before — logic in view
def reserve_seat(request, seat_id):
    seat = Seat.objects.get(pk=seat_id)
    if seat.is_reserved:
        ...

# after — logic in service
# cinema/services.py
def reserve_seat(seat_id, user):
    seat = Seat.objects.select_for_update().get(pk=seat_id)
    ...

# cinema/views.py
def reserve_seat_view(request, seat_id):
    result = services.reserve_seat(seat_id, request.user)
    ...
```

**Extract selector**: if the same queryset filter is used in multiple places, move it to `cinema/selectors.py`.

**Simplify view**: if a view is doing too much, split it. One URL, one responsibility.

## After refactoring

- Run `uv run pytest --cov` — coverage should not drop.
- Run `uv run pylint cinema` and `uv run black .`.
- If behavior is unchanged, no new tests are required — but existing tests must still pass.
