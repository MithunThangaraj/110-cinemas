## Why

Exercise 10 asks for one dynamic, server-driven interaction using HTMX. The
most natural fit in this app is seat reservation: right now, reserving a seat
takes the visitor through two full-page navigations (seat grid → reservation
form page → confirmation page) just to flip one seat from "available" to
"reserved". That's exactly the kind of small, localized state change HTMX is
for — one of the exercise's own suggested examples is "changing available
seats after a selection".

## What Changes

- On the seat selection page, clicking an available seat's "Reserve" link now
  issues an HTMX `GET` that swaps just that seat's grid cell for an inline
  reservation form (name + email) — no full-page navigation.
- Submitting that form issues an HTMX `POST` to the same URL. The seat's grid
  cell is swapped again:
  - invalid input → the form re-renders in place with validation errors;
  - seat successfully reserved → the cell swaps to show "reserved" (matching
    every other unavailable seat), plus an `HX-Trigger` fires a toast-style
    confirmation rendered via the existing messages area;
  - seat taken by someone else in the meantime (race) → the cell swaps to
    "reserved" with a short explanation, instead of redirecting away.
- **Non-HTMX requests are unaffected**: a request without the `HX-Request`
  header (direct browser navigation, JS disabled, or a bookmark) still gets
  the existing full-page GET-form/POST-process/redirect behavior from
  Exercise 8. This is progressive enhancement, not a replacement.
- Wires up `django-htmx` (already a declared dependency, never installed):
  adds `django_htmx` to `INSTALLED_APPS` and `HtmxMiddleware` to
  `MIDDLEWARE` so `request.htmx` is available.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `web-views`: the "Reserve seat action" requirement gains HTMX-aware
  behavior — an `HX-Request` changes what `GET`/`POST` on
  `/seats/<seat_id>/reserve/` return (a partial seat-grid cell instead of a
  full page / redirect).

## Impact

- Modified files: `cinema/settings.py` (django-htmx wiring),
  `cinema/views.py`, `cinema/templates/cinema/_seat.html`,
  `cinema/templates/cinema/seat_selection.html`.
- New file: `cinema/templates/cinema/_seat_reserve_form.html` (the partial
  swapped in when reserving).
- No new dependency (django-htmx was already declared), no migrations.
