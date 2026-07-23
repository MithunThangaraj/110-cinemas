## MODIFIED Requirements

### Requirement: Seat selection page
The system SHALL expose `GET /screenings/<screening_id>/seats/`
(name: `seat-selection`) taking a `screening_id` (integer, path parameter) and
returning an HTML page that shows every seat for that screening as a seat map,
where each available seat is a selectable control and reserved seats are shown
as unavailable. The page SHALL also show a single reservation form (customer
name and email) used to reserve the currently selected seat.

#### Scenario: Viewing seats for an existing screening
- **WHEN** a browser sends `GET /screenings/<screening_id>/seats/` for a screening
  that exists
- **THEN** the response SHALL be HTTP 200 with an HTML page listing all of that
  screening's seats, marking each as available or reserved, and including a
  name/email reservation form

#### Scenario: Viewing seats for a non-existent screening
- **WHEN** a browser sends `GET /screenings/<screening_id>/seats/` for a
  `screening_id` that does not exist
- **THEN** the response SHALL be HTTP 404

### Requirement: Reserve seat action
The system SHALL expose `POST /screenings/<screening_id>/reserve/`
(name: `reserve-seats`) taking a `screening_id` (integer, path parameter). The
chosen seat is submitted as a `seat` form field together with the customer's
name and email. The view SHALL validate that a seat belonging to the screening
was chosen and that the name (required) and email (required, well-formed) are
valid.

Behavior depends on whether the request carries the `HX-Request` header:

**Non-HTMX requests:**
- On success, it SHALL reserve the seat, store the reservation's booking ID in
  the session (so it appears in "My Bookings"), add a success flash message,
  and redirect (HTTP 302) to the reservation confirmation page.
- On any validation problem — no seat chosen, invalid name/email, or the seat
  was already taken — it SHALL re-render the full seat selection page (HTTP 200)
  with an error message and create no reservation.

**HTMX requests** (`HX-Request` header present):
- On success, it SHALL reserve the seat, store the booking ID in the session,
  and return a client redirect (an `HX-Redirect` response) to the reservation
  confirmation page.
- On any validation problem, it SHALL return only the reservation-area HTML
  fragment (HTTP 200) re-rendered with an error message and no reservation,
  which the client swaps in place without a full page reload.

#### Scenario: Reserving a chosen seat (non-HTMX)
- **WHEN** a browser sends a valid `POST /screenings/<id>/reserve/` with a
  `seat` field for an available seat plus a valid name and email, without an
  `HX-Request` header
- **THEN** a confirmed reservation SHALL be created for that seat with the
  submitted name and email, its booking ID SHALL be stored in the session, and
  the response SHALL redirect to the URL named `reservation-confirmation`

#### Scenario: Reserving a chosen seat (HTMX)
- **WHEN** a browser sends the same valid request with an `HX-Request` header
- **THEN** the reservation SHALL be created and the response SHALL be an
  `HX-Redirect` to the reservation confirmation page

#### Scenario: Submitting without choosing a seat
- **WHEN** a browser sends `POST /screenings/<id>/reserve/` with valid name and
  email but no `seat` field
- **THEN** no reservation SHALL be created and the response SHALL show an error
  asking the visitor to choose a seat (a full page for non-HTMX, the
  reservation-area fragment for HTMX)

#### Scenario: Submitting an invalid name or email
- **WHEN** a browser sends `POST /screenings/<id>/reserve/` with a chosen seat
  but a missing name or malformed email
- **THEN** no reservation SHALL be created and the response SHALL re-render the
  reservation form with validation errors

#### Scenario: Reserving a seat that was just taken
- **WHEN** a browser sends a valid `POST /screenings/<id>/reserve/` for a seat
  that already has a confirmed reservation
- **THEN** no new reservation SHALL be created and the response SHALL show an
  error telling the visitor to choose another seat, with the seat map reflecting
  that the seat is now reserved
