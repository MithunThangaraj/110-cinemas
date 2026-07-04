## Why

The database schema exists but the project has no HTTP-facing behavior yet — there
are no views and no non-admin URLs. To turn this into a working web application we
need a first, minimal set of view functions covering the core user actions: browsing
movies, picking a seat, and reserving it.

## What Changes

- Add `cinema/views.py` with basic view functions:
  - `index`: redirects to the movie list (home page entry point).
  - `movie_list`: lists all movies.
  - `seat_selection`: shows the seats for a screening (form page for reserving one).
  - `reserve_seat_view`: processes the seat reservation form submission and redirects
    to a confirmation page.
  - `reservation_confirmation`: shows the outcome of a reservation attempt.
- Add corresponding URL patterns (named routes) to `cinema/urls.py`.
- Add minimal templates under `cinema/templates/cinema/` (`base.html`,
  `movie_list.html`, `seat_selection.html`, `reservation_confirmation.html`).
- Views are intentionally minimal: no styling, no HTMX partials, no auth yet — those
  are follow-up exercises. Reservation failures are shown as a plain message rather
  than a polished error page.

## Capabilities

### New Capabilities
- `web-views`: the URL-addressable views a browser can hit (home, movie list, seat
  selection, reservation processing, reservation confirmation) — their routes,
  arguments, and what each returns.

### Modified Capabilities
- None. This exposes the existing data model over HTTP; it doesn't change any data
  model requirements.

## Impact

- New files: `cinema/views.py`, `cinema/templates/cinema/*.html`.
- Modified files: `cinema/urls.py`.
- Depends on existing `cinema/models.py` and `cinema/services.py` (`reserve_seat`).
- No new dependencies, no migrations.
