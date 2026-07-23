## 1. Wire up django-htmx

- [x] 1.1 Add `django_htmx` to `INSTALLED_APPS`
- [x] 1.2 Add `django_htmx.middleware.HtmxMiddleware` to `MIDDLEWARE`

## 2. Templates

- [x] 2.1 Add `cinema/templates/cinema/_seat_reserve_form.html`: the seat's
      `<li>` with an inline reservation form, `hx-post` back to the same URL,
      `hx-target="closest li"`, `hx-swap="outerHTML"`
- [x] 2.2 Update `_seat.html`: the "Reserve" link gains `hx-get` to the
      reserve-seat URL, `hx-target="closest li"`, `hx-swap="outerHTML"`
- [x] 2.3 Load the HTMX script in `base.html`

## 3. View logic

- [x] 3.1 `reserve_seat_view`: branch on `request.htmx` for both GET and POST
- [x] 3.2 HTMX GET renders `_seat_reserve_form.html`
- [x] 3.3 HTMX POST (invalid) re-renders `_seat_reserve_form.html` with errors
- [x] 3.4 HTMX POST (success) renders `_seat.html` for the now-reserved seat
- [x] 3.5 HTMX POST (already reserved) renders `_seat.html` in reserved state
- [x] 3.6 Non-HTMX behavior (Exercise 8) is unchanged

## 4. Tests

- [x] 4.1 Add HTMX-header test cases to `cinema/test_views.py` covering all
      scenarios in the spec delta
- [x] 4.2 Confirm existing non-HTMX tests still pass unchanged

## 5. Verification

- [x] 5.1 Run `uv run pytest --cov` and confirm all tests pass
- [x] 5.2 Run `uv run black .` and `uv run pylint cinema`
- [x] 5.3 Manually verify in the browser: clicking "Reserve" swaps the seat
      cell in place (no page navigation, no full reload) end to end
