## 1. Routing and views

- [x] 1.1 Replace `reserve-seat` (`/seats/<id>/reserve/`) with `reserve-seats`
      (`/screenings/<id>/reserve/`) in `cinema/urls.py`
- [x] 1.2 Rewrite `reserve_seats` view: read `seat` from POST, validate seat +
      form, branch on `request.htmx` (client redirect on success, partial on
      error), keep non-HTMX redirect/flash fallback

## 2. Templates

- [x] 2.1 Add `_reservation_area.html` (the whole reservation `<form>`: seat
      map + checkout, `hx-post` targeting itself)
- [x] 2.2 Rewrite `_seat.html`: radio label for available seats, inert span for
      reserved
- [x] 2.3 Simplify `seat_selection.html` to include the reservation area
- [x] 2.4 Remove `reservation_form.html` and `_seat_reserve_form.html`

## 3. Styles

- [x] 3.1 Restyle seats as radio-label boxes with a `:has(input:checked)`
      selected state; add checkout-box styling

## 4. Tests

- [x] 4.1 Rewrite reservation tests for the screening-scoped endpoint and the
      new selection/checkout flow (non-HTMX and HTMX paths)

## 5. Verification

- [x] 5.1 `uv run pytest --cov` passes
- [x] 5.2 `uv run black .` and `uv run pylint cinema`
- [x] 5.3 Verify in browser: select highlights instantly, checkout reserves and
      redirects, no-seat submit shows an inline error without navigating
