# web-views Specification

## Purpose
TBD - created by archiving change write-view-functions. Update Purpose after archive.
## Requirements
### Requirement: Home redirect
The system SHALL expose `GET /` (name: `index`) that takes no arguments and
redirects (HTTP 302) to the movie list page.

#### Scenario: Visiting the root URL
- **WHEN** a browser sends `GET /`
- **THEN** the response SHALL be a redirect to the URL named `movie-list`

### Requirement: Movie list page
The system SHALL expose `GET /movies/` (name: `movie-list`) that returns an HTML
page listing movies (title and release date) and a search form. It SHALL accept
an optional `q` query parameter (a title search) submitted via a **GET** form;
when `q` is provided, the list SHALL be filtered to movies whose title contains
`q` (case-insensitive).

#### Scenario: Listing movies
- **WHEN** a browser sends `GET /movies/`
- **THEN** the response SHALL be HTTP 200 with an HTML page containing the title
  of every `Movie` in the database

#### Scenario: Searching movies by title
- **WHEN** a browser sends `GET /movies/?q=<term>`
- **THEN** the response SHALL be HTTP 200 listing only movies whose title
  contains `<term>` (case-insensitive)

### Requirement: Seat selection page
The system SHALL expose `GET /screenings/<screening_id>/seats/`
(name: `seat-selection`) taking a `screening_id` (integer, path parameter) and
returning an HTML page listing every seat for that screening with its
availability, and a way to submit a reservation for each available seat.

#### Scenario: Viewing seats for an existing screening
- **WHEN** a browser sends `GET /screenings/<screening_id>/seats/` for a screening
  that exists
- **THEN** the response SHALL be HTTP 200 with an HTML page listing all of that
  screening's seats and whether each is available

#### Scenario: Viewing seats for a non-existent screening
- **WHEN** a browser sends `GET /screenings/<screening_id>/seats/` for a
  `screening_id` that does not exist
- **THEN** the response SHALL be HTTP 404

### Requirement: Reserve seat action
The system SHALL expose `/seats/<seat_id>/reserve/` (name: `reserve-seat`)
taking a `seat_id` (integer, path parameter):
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

Flash messages are stored using Django's session-backed `messages` framework
and rendered by the shared base layout on the next page.

#### Scenario: Requesting the reservation form
- **WHEN** a browser sends `GET /seats/<seat_id>/reserve/` for a seat
- **THEN** the response SHALL be HTTP 200 with a form for the customer's name and
  email

#### Scenario: Submitting an invalid reservation form
- **WHEN** a browser sends `POST /seats/<seat_id>/reserve/` with a missing name
  or a malformed email
- **THEN** no reservation SHALL be created and the response SHALL be HTTP 200
  re-rendering the form with validation errors

#### Scenario: Reserving an available seat
- **WHEN** a browser sends a valid `POST /seats/<seat_id>/reserve/` for an
  available seat
- **THEN** a confirmed reservation SHALL be created for that seat with the
  submitted customer name and email, the reservation's booking ID SHALL be
  stored in the session, and the response SHALL redirect to the URL named
  `reservation-confirmation` for the new reservation's ID

#### Scenario: Reserving an already-reserved seat
- **WHEN** a browser sends a valid `POST /seats/<seat_id>/reserve/` for a seat
  that already has a confirmed reservation
- **THEN** no new reservation SHALL be created and the response SHALL redirect
  to the seat selection page for that seat's screening, carrying an error flash
  message

### Requirement: Reservation confirmation page
The system SHALL expose `GET /reservations/<reservation_id>/`
(name: `reservation-confirmation`) taking a `reservation_id` (integer, path
parameter) and returning an HTML page showing that reservation's booking ID,
seat, and status.

#### Scenario: Viewing a confirmation for an existing reservation
- **WHEN** a browser sends `GET /reservations/<reservation_id>/` for a
  reservation that exists
- **THEN** the response SHALL be HTTP 200 with an HTML page showing the
  reservation's booking ID, seat, and status

### Requirement: My bookings page
The system SHALL expose `GET /my-bookings/` (name: `my-bookings`) that takes no
arguments and returns an HTML page listing the reservations whose booking IDs
are stored in the current session, each linking to its confirmation page. This
lets a visitor review the seats they reserved during the current visit without
an account.

#### Scenario: Viewing bookings made this session
- **WHEN** a browser sends `GET /my-bookings/` after reserving one or more seats
  in the same session
- **THEN** the response SHALL be HTTP 200 with an HTML page listing those seats

#### Scenario: Viewing bookings with an empty session
- **WHEN** a browser sends `GET /my-bookings/` without having reserved any seat
- **THEN** the response SHALL be HTTP 200 with an HTML page indicating there are
  no bookings yet

