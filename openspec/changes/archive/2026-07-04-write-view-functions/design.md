## Context

The project has models and services (`reserve_seat`, `cancel_reservation`) but no
views or URLs beyond `/admin/`. This is the first pass at the presentation layer, so
the design is deliberately small.

## Goals / Non-Goals

**Goals:**
- One view per user action, each reachable by a named URL.
- Use existing `services.reserve_seat` rather than duplicating booking logic in the view.
- Keep templates minimal (plain HTML, no HTMX yet, no styling).

**Non-Goals:**
- HTMX partials / dynamic interaction (a later exercise).
- Authentication or per-user reservation history.
- Handling seat-selection UI polish (checkbox grids, JS) — a plain list of seats
  with a "Reserve" link/button per available seat is enough for now.
- Cancelling reservations from the UI (the service exists; no view wired to it yet).

## Decisions

- **Function-based views**, matching `django-patterns`/`django-expert` conventions
  for this project (class-based views are reserved for later CRUD-heavy screens).
- **POST-redirect-GET** for the reservation flow: `seat_selection` (GET, form page)
  → `reserve_seat_view` (POST, processes and redirects) → `reservation_confirmation`
  (GET, shows the result). This avoids duplicate reservations on page refresh.
- **Errors surfaced via query string**, not a dedicated error page: if
  `services.reserve_seat` raises `ValidationError` (seat already taken),
  `reserve_seat_view` redirects back to `seat_selection` for that seat's screening
  with `?error=1`, and the template renders a failure message so the user can pick a
  different seat. Simpler than the Django messages framework for this exercise; can
  be revisited once HTMX partials are introduced.
- **No hard-coded IDs**: routes take real `movie_id` / `screening_id` / `seat_id`
  path parameters resolved against the DB, since the models already support this —
  hard-coding would just make the views harder to test.

## Risks / Trade-offs

- [No validation that a seat belongs to the screening shown in the seat_selection
  page it was reserved from] → Acceptable for now; `reserve_seat` still enforces
  seat-level availability via `select_for_update()`.
- [No CSRF-safe confirmation dialog before booking] → Standard Django CSRF
  protection on the POST form is sufficient at this stage.
