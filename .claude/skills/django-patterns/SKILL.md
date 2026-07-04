---
name: django-patterns
description: Use when deciding how to structure code in this Django project — where logic lives, how to organize services, how HTMX fits in, and how to keep the codebase consistent.
---

# Django Patterns

Structural conventions for this project.

## Where logic lives

- **Models**: data shape and simple properties only. No business logic.
- **Views**: handle HTTP — parse request, call service, return response. Stay thin.
- **Services (if added)**: a `services.py` module per app for multi-step business operations (e.g. `reserve_seat`, `cancel_booking`). Call these from views, not the other way around.
- **Selectors (if added)**: a `selectors.py` module for reusable queryset logic. Views call selectors, not raw ORM.

## HTMX patterns

- Every HTMX-triggered view should check `request.htmx` and return a partial if true, or a full page if false (for direct browser access).
- Partial templates are named with a `_partial` suffix, e.g. `seat_grid_partial.html`.
- Use `hx-target` to specify where the response is injected; keep targets as specific as possible.
- Use `hx-swap="outerHTML"` for replacing a component, `innerHTML` for updating contents.
- For form submissions, prefer `hx-post` + return a partial with updated state over full-page redirects.

## File organization

```
cinema/
├── models.py
├── views.py
├── urls.py
├── forms.py
├── admin.py
├── services.py      # business logic (add if needed)
├── selectors.py     # query logic (add if needed)
├── templates/
│   └── cinema/
│       ├── base.html
│       └── ...
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_services.py
```

## Testing conventions

- Use `pytest-django` — never Django's `TestCase` directly.
- Use `@pytest.mark.django_db` on tests that touch the database.
- Use `client` fixture for view tests.
- Test HTMX views with `headers={"HX-Request": "true"}` in the client call.
- Factory pattern (manual or with a factory helper) for creating test data — not fixtures files.
