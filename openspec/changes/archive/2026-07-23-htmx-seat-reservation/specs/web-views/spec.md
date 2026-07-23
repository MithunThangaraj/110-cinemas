## MODIFIED Requirements

### Requirement: Reserve seat action
The system SHALL expose `/seats/<seat_id>/reserve/` (name: `reserve-seat`)
taking a `seat_id` (integer, path parameter). Behavior depends on whether the
request carries the `HX-Request` header (an HTMX request):

**Non-HTMX requests** (direct navigation, HTMX disabled):
- On **GET**, it SHALL return an HTML page with a reservation form asking for the
  customer's name and email.
- On **POST**, it SHALL validate the submitted form (name required; email
  required and well-formed) and:
  - if the form is invalid, re-render the reservation form (HTTP 200) with
    errors and create no reservation;
  - if valid, call the existing seat reservation logic, storing the customer's
    name and email on the reservation;
    - on success, record the new reservation's booking ID in the session (so it
      appears in "My Bookings"), add a success flash message, and redirect
      (HTTP 302) to the reservation confirmation page;
    - on failure (seat already reserved), add an error flash message and
      redirect (HTTP 302) back to the seat selection page for that screening.

**HTMX requests** (`HX-Request` header present):
- On **GET**, it SHALL return an HTML fragment (HTTP 200) containing just that
  seat's grid cell, replaced with an inline reservation form.
- On **POST**, it SHALL validate the submitted form the same way and return an
  HTML fragment (HTTP 200) for just that seat's grid cell:
  - if the form is invalid, the fragment SHALL be the inline form re-rendered
    with errors, and no reservation is created;
  - if valid and the seat is still available, the fragment SHALL be that
    seat's cell in its "reserved" state, with a confirmed reservation created
    and its booking ID stored in the session;
  - if valid but the seat was reserved by someone else in the meantime, the
    fragment SHALL be that seat's cell in its "reserved" state (no new
    reservation is created).

Flash messages (non-HTMX path) are stored using Django's session-backed
`messages` framework and rendered by the shared base layout on the next page.

#### Scenario: Requesting the reservation form (non-HTMX)
- **WHEN** a browser sends `GET /seats/<seat_id>/reserve/` for a seat, without
  an `HX-Request` header
- **THEN** the response SHALL be HTTP 200 with a full HTML page containing a
  form for the customer's name and email

#### Scenario: Requesting the reservation form (HTMX)
- **WHEN** a browser sends `GET /seats/<seat_id>/reserve/` for an available
  seat, with an `HX-Request` header
- **THEN** the response SHALL be HTTP 200 with an HTML fragment for just that
  seat's grid cell, containing the reservation form

#### Scenario: Submitting an invalid reservation form (HTMX)
- **WHEN** a browser sends `POST /seats/<seat_id>/reserve/` with a missing
  name or malformed email, with an `HX-Request` header
- **THEN** no reservation SHALL be created and the response SHALL be an HTML
  fragment for that seat's cell, re-rendering the form with validation errors

#### Scenario: Reserving an available seat (HTMX)
- **WHEN** a browser sends a valid `POST /seats/<seat_id>/reserve/` for an
  available seat, with an `HX-Request` header
- **THEN** a confirmed reservation SHALL be created with the submitted
  customer name and email, its booking ID SHALL be stored in the session, and
  the response SHALL be an HTML fragment showing that seat's cell in its
  "reserved" state

#### Scenario: Reserving an already-reserved seat (HTMX)
- **WHEN** a browser sends a valid `POST /seats/<seat_id>/reserve/` for a seat
  that already has a confirmed reservation, with an `HX-Request` header
- **THEN** no new reservation SHALL be created and the response SHALL be an
  HTML fragment showing that seat's cell in its "reserved" state

#### Scenario: Submitting an invalid reservation form (non-HTMX)
- **WHEN** a browser sends `POST /seats/<seat_id>/reserve/` with a missing name
  or a malformed email, without an `HX-Request` header
- **THEN** no reservation SHALL be created and the response SHALL be HTTP 200
  re-rendering the full form page with validation errors

#### Scenario: Reserving an available seat (non-HTMX)
- **WHEN** a browser sends a valid `POST /seats/<seat_id>/reserve/` for an
  available seat, without an `HX-Request` header
- **THEN** a confirmed reservation SHALL be created for that seat with the
  submitted customer name and email, the reservation's booking ID SHALL be
  stored in the session, and the response SHALL redirect to the URL named
  `reservation-confirmation` for the new reservation's ID

#### Scenario: Reserving an already-reserved seat (non-HTMX)
- **WHEN** a browser sends a valid `POST /seats/<seat_id>/reserve/` for a seat
  that already has a confirmed reservation, without an `HX-Request` header
- **THEN** no new reservation SHALL be created and the response SHALL redirect
  to the seat selection page for that seat's screening, carrying an error flash
  message
