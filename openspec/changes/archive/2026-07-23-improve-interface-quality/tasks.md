## 1. Stylesheet

- [x] 1.1 Add `cinema/static/cinema/css/styles.css`, link it from `base.html`
- [x] 1.2 Remove any inline styling; base layout (header/nav/main/footer),
      colors, spacing, and typography live in the stylesheet only

## 2. Semantic HTML pass

- [x] 2.1 `base.html`: viewport meta tag, skip-to-content link, `<footer>`,
      `aria-live="polite"` on the messages list
- [x] 2.2 `movie_list.html` / `_movie_card.html`: proper `<label>` for the
      search input, correct heading nesting
- [x] 2.3 `seat_selection.html` / `_seat.html`: wrap the seat grid in a
      `<fieldset>`/`<legend>`
- [x] 2.4 `reservation_form.html` / `reservation_confirmation.html` /
      `my_bookings.html`: labels linked to inputs, correct heading nesting

## 3. Responsive layout

- [x] 3.1 Mobile-first CSS: single-column layout by default
- [x] 3.2 One `@media (min-width: ...)` breakpoint: seat grid becomes a
      multi-column CSS grid, movie list becomes a wider layout

## 4. Accessibility

- [x] 4.1 Visible `:focus` states on links, buttons, and inputs
- [x] 4.2 Confirm text/background color contrast is readable
- [x] 4.3 `alt` text wherever an image appears

## 5. Verification

- [x] 5.1 Run `uv run pytest --cov` and confirm all tests still pass
      (no behavior changed, so no test changes expected)
- [x] 5.2 Run `uv run black .` and `uv run pylint cinema`
- [x] 5.3 Manually check the app in the browser at mobile and desktop widths,
      and tab through each page with the keyboard only
