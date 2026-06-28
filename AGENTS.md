# AGENTS.md

## Project scope

This is a Django + HTMX app for browsing movies and reserving cinema seats.

Main app:

- `cinema/` — movies, screenings, seat reservations, and the web UI

## Important project conventions

- Keep views thin; move business logic into service functions or helper modules.
- Use HTMX for dynamic updates — return partial HTML responses, not full pages, where possible.
- Templates live in `cinema/templates/cinema/`.
- Use class-based views for standard CRUD; function-based views are fine for HTMX partials.

## Commands

- Run server: `uv run python manage.py runserver`
- Run tests: `uv run pytest --cov`
- Lint: `uv run pylint cinema`
- Format: `uv run black .`
- Create migrations: `uv run python manage.py makemigrations`
- Apply migrations: `uv run python manage.py migrate`

## Things that are easy to break

- Seat reservation logic — concurrent bookings can cause double-booking if not handled carefully.
- HTMX partial responses — returning a full page instead of a partial will break the UI.
- URL names — used in templates with `{% url %}` tags; renaming breaks templates silently.

## Change coupling

If you change:

- a model → also check and update migrations, admin registration, and any related templates
- a URL name → search all templates for `{% url '<name>' %}` and update them
- a view that returns HTMX partials → verify the `HX-Request` header check is still in place
- seat availability logic → also check reservation creation and cancellation paths

## Constraints

- Always use `uv run` — never call `python`, `pytest`, or `black` directly.
- Do not edit old migrations; create a new one instead.
- Do not install new packages without confirming with the user. Use `uv add <pkg>` if approved.
- Prefer small, targeted changes over broad refactors.

## Documentation use

- Use `openspec/specs/*` as the canonical source for technical and runtime documentation.
- For project-level conventions, check the `context` section of `openspec/config.yaml`.
- For feature-specific details, read `openspec/specs/<capability>/spec.md`.
- Use `openspec/notes/*` as supplemental context only — non-normative ideas and backlog.
- If code and documentation are inconsistent, report it and suggest a fix.
- When a new feature is added or a system fact is discovered, suggest reflecting it in the specs.

## Testing expectations

Add or update tests for:

- any change to reservation or seat availability logic
- new views or URL routes
- model method changes
- any permission or access control logic
