## 1. Views and URLs

- [x] 1.1 Create `cinema/views.py` with `index`, `movie_list`, `seat_selection`,
      `reserve_seat_view`, and `reservation_confirmation` view functions
- [x] 1.2 Add named URL patterns for all five views to `cinema/urls.py`

## 2. Templates

- [x] 2.1 Add `cinema/templates/cinema/base.html` with a `{% block %}`-based layout
- [x] 2.2 Add `movie_list.html` listing movies with links to their screenings
- [x] 2.3 Add `seat_selection.html` listing seats with a reserve form per available
      seat, and an error message when `?error=1` is present
- [x] 2.4 Add `reservation_confirmation.html` showing booking ID, seat, and status

## 3. Tests

- [x] 3.1 Add `cinema/test_views.py` covering: home redirect, movie list contents,
      seat selection for existing/missing screening, reserving an available seat,
      reserving an already-reserved seat, and the confirmation page

## 4. Verification

- [x] 4.1 Run `uv run pytest --cov` and confirm all tests pass
- [x] 4.2 Run `uv run black .` and `uv run pylint cinema`
- [x] 4.3 Manually run `uv run python manage.py runserver` and click through
      movie list → seat selection → reserve → confirmation
