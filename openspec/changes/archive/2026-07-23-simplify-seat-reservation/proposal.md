## Why

The Exercise-10 reservation flow reserved seats one at a time by expanding an
inline name/email form *inside* the clicked seat's grid cell. In practice this
is annoying: every seat click immediately demands name + email and reshapes the
seat map. Real cinema booking UIs separate *selecting* a seat from *entering
your details*.

## What Changes

- Replace per-seat inline forms with **radio-button seats**. Clicking an
  available seat just selects it (highlights), instantly, with no form and no
  reflow of the map. Reserved seats render as non-interactive.
- Add a single **checkout box below the map** with name + email fields and one
  "Reserve seat" button. Details are entered once, not per seat.
- The reservation endpoint becomes screening-scoped: the chosen seat is a form
  field (`seat`) rather than a path parameter.
- Keep the HTMX enhancement: submitting posts via HTMX and, on success,
  client-redirects to the confirmation page; on any validation problem
  (no seat chosen, bad email, missing name, or the seat was just taken) the
  reservation area is re-rendered in place with an error and no full reload.
- **BREAKING** (internal): the `reserve-seat` route (`/seats/<id>/reserve/`) is
  replaced by `reserve-seats` (`/screenings/<id>/reserve/`). The inline-form
  templates (`reservation_form.html`, `_seat_reserve_form.html`) are removed.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `web-views`: the "Seat selection page" and "Reserve seat action" requirements
  change to describe the select-then-checkout flow and the new
  screening-scoped reserve endpoint.

## Impact

- Modified: `cinema/urls.py`, `cinema/views.py`,
  `cinema/templates/cinema/seat_selection.html`,
  `cinema/templates/cinema/_seat.html`,
  `cinema/static/cinema/css/styles.css`, `cinema/test_views.py`.
- New: `cinema/templates/cinema/_reservation_area.html`.
- Removed: `cinema/templates/cinema/reservation_form.html`,
  `cinema/templates/cinema/_seat_reserve_form.html`.
- No new dependencies, no migrations.
