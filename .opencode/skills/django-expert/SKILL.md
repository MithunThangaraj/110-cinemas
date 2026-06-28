---
name: django-expert
description: Use when working on Django models, views, URLs, forms, admin, middleware, or any Django-specific architecture question. Covers Django 6 patterns for this project.
---

# Django Expert

You are working on a Django 6 project using uv for package management. Apply these patterns consistently.

## Models

- Define `__str__` on every model.
- Use `verbose_name` and `verbose_name_plural` in `Meta`.
- Add `db_index=True` on fields used in `filter()` or `order_by()` frequently.
- Use `select_related` and `prefetch_related` to avoid N+1 queries.
- Never put business logic in models — keep them as data containers.

## Views

- Class-based views for standard CRUD (ListView, DetailView, CreateView, UpdateView, DeleteView).
- Function-based views for HTMX partials — they're simpler and easier to read.
- Check `request.htmx` (provided by django-htmx) to decide whether to return a partial or full response.
- Return `HttpResponseClientRedirect` or `HttpResponseClientRefresh` for HTMX post-redirect patterns.

## URLs

- Always name every URL pattern.
- Use `app_name` in `urls.py` for namespacing.
- Never hardcode paths in views or templates — always use `reverse()` or `{% url %}`.

## Templates

- Templates go in `cinema/templates/cinema/`.
- Use `{% block %}` inheritance from a base template.
- HTMX partial templates should be standalone fragments, not full pages.

## Forms

- Use Django ModelForms wherever the form maps directly to a model.
- Add `clean_<field>()` methods for field-level validation.
- Add `clean()` for cross-field validation.

## Admin

- Register every model with `@admin.register`.
- Set `list_display`, `list_filter`, and `search_fields` on every ModelAdmin.

## Migrations

- Never edit existing migrations.
- Always run `uv run python manage.py makemigrations` after changing a model.
- Keep migration names descriptive: `uv run python manage.py makemigrations --name add_screening_capacity`.
