## Context

`cinema/views.py` currently has `reserve_seat_view` handling GET (render form)
and POST (validate, reserve, redirect) for full-page navigation only. HTMX is
a declared `pyproject.toml` dependency (`django-htmx`) but was never actually
wired into `settings.py`, so `request.htmx` doesn't exist yet anywhere in the
app. `AGENTS.md` already documents the convention this change follows:
"Is `request.htmx` checked before returning partials?" and "returning a full
page instead of a partial will break the UI".

## Goals / Non-Goals

**Goals:**
- Answer the exercise's four design questions concretely (see Decisions).
- Keep the non-HTMX path (Exercise 8's full-page flow) completely intact.

**Non-Goals:**
- Converting every view to HTMX partials — just this one interaction.
- Real-time updates from *other* visitors (if seat B2 gets taken by someone
  else, your page won't know until you interact with it again).

## Decisions

Answering the exercise's four questions directly:

- **What updates dynamically without a full reload?** The seat grid cell for
  the seat being reserved — nothing else on the page changes.
- **What triggers the update?** Two triggers on the same seat cell:
  1. `hx-get` on the "Reserve" link — swaps the cell for the reservation form.
  2. `hx-post` on that form's submit — swaps the cell for the result (now
     "reserved", or the form again with errors).
- **Which part of the page is updated?** Only the `<li class="seat">` for
  that one seat (`hx-target="closest li"`, `hx-swap="outerHTML"`). The rest
  of the seat grid, the header, and the page's messages area are untouched.
- **What does the server return?** `reserve_seat_view` branches on
  `request.htmx`:
  - HTMX **GET** → renders `_seat_reserve_form.html` (just the `<li>` with an
    inline form), not the full `reservation_form.html` page.
  - HTMX **POST**, invalid → re-renders `_seat_reserve_form.html` with errors.
  - HTMX **POST**, seat reserved successfully → renders `_seat.html` for the
    now-reserved seat (same partial the seat grid already uses). The seat
    visibly flipping from an open form to "reserved" *is* the confirmation —
    no separate flash message needed for this path.
  - HTMX **POST**, seat already taken → renders `_seat.html` in its reserved
    state (someone beat you to it) with an inline note, rather than
    redirecting to seat selection with a flash message (there's no page
    navigation to attach a flash message to).
  - **Non-HTMX** request (no `HX-Request` header) → exactly the Exercise 8
    behavior: full `reservation_form.html` page on GET, redirect + Django
    `messages` on POST.
- **Progressive enhancement via `request.htmx`, not JS feature-detection.**
  `django-htmx`'s `request.htmx` is a clean boolean the view already needs to
  branch on regardless of how the client got there (matches the existing
  `AGENTS.md` convention for this project rather than introducing a new one).
## Risks / Trade-offs

- [Double implementation: full-page path and HTMX path both exist in
  `reserve_seat_view`] → Necessary for progressive enhancement; kept small by
  reusing the same `services.reserve_seat` call and the same `ReservationForm`
  for both paths.
- [A visitor reserving via HTMX never sees a shareable confirmation URL] →
  Acceptable; "My Bookings" (session-based) still lists it, and the
  non-HTMX path still redirects to a confirmation page for anyone who wants
  one (e.g., HTMX disabled).
