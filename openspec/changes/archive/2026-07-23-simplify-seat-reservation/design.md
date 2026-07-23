## Context

Exercise 10 wired seat reservation through per-seat HTMX GET/POST on
`/seats/<id>/reserve/`, swapping the clicked seat cell into an inline form and
back. It worked but the UX was intrusive. This change keeps the HTMX value
while adopting the standard "pick seat → checkout" pattern.

## Goals / Non-Goals

**Goals:**
- Selecting a seat is instant and does not demand details or move the map.
- Enter name/email once, in one place.
- Preserve a meaningful HTMX interaction (async submit + in-place errors) and
  a working non-HTMX fallback.

**Non-Goals:**
- Multi-seat selection (still one seat per reservation).
- Accounts/auth.

## Decisions

- **Radio inputs for seats.** Each available seat is a `<label>` wrapping a
  visually-hidden `<input type="radio" name="seat">`; reserved seats are inert
  `<span>`s. Selection is pure HTML — no JS, no server round-trip — and the
  selected state is styled with `.seat--available:has(input:checked)`. This is
  also good for accessibility: the seat grid is a `<fieldset>`, each seat a
  labelled radio, unavailable seats simply absent from the radio group.
- **One screening-scoped endpoint.** Because the seat is now a form field, the
  reserve route is `POST /screenings/<id>/reserve/` (name `reserve-seats`)
  rather than seat-in-path. The whole reservation `<form>` (map + checkout)
  posts together.
- **HTMX targets the whole reservation area.** `hx-post` with
  `hx-target="this" hx-swap="outerHTML"` on the form. On validation problems
  the server returns `_reservation_area.html` (the form partial) with the error
  and the previously chosen seat still selected; HTMX swaps it in with no full
  reload. On success the server returns `HttpResponseClientRedirect` to the
  confirmation page.
- **Non-HTMX fallback.** Without `HX-Request`, the same view re-renders the
  full `seat_selection.html` on error and issues a normal 302 redirect (plus a
  flash message) on success — progressive enhancement, unchanged in spirit from
  Exercise 8/10.
- **"Seat just taken" is a validation outcome, not a crash.** Even with a valid
  form the seat can be taken by another visitor between selection and submit;
  `services.reserve_seat` raises `ValidationError`, which the view turns into an
  in-area error message with the map refreshed to show the seat as reserved.

## Risks / Trade-offs

- [`:has()` is required for the selected-seat highlight] → Acceptable; it is
  supported in all current browsers, and selection still functions without it
  (the radio is still checked; only the visual highlight would be missing).
- [Losing the per-seat HTMX swap from Exercise 10] → The dynamic, server-driven
  partial update is retained, just relocated to the reservation-area submit and
  its error handling, which is a cleaner interaction.
