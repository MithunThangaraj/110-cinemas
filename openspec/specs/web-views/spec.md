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
The system SHALL expose `GET /movies/` (name: `movie-list`) that takes no
arguments and returns an HTML page listing all movies (title and release date).

#### Scenario: Listing movies
- **WHEN** a browser sends `GET /movies/`
- **THEN** the response SHALL be HTTP 200 with an HTML page containing the title
  of every `Movie` in the database

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

#### Scenario: Seat selection page shows a reservation error
- **WHEN** a browser sends `GET /screenings/<screening_id>/seats/?error=1`
- **THEN** the response SHALL be HTTP 200 with the page additionally showing a
  message that the last reservation attempt failed

### Requirement: Reserve seat action
The system SHALL expose `POST /seats/<seat_id>/reserve/` (name: `reserve-seat`)
taking a `seat_id` (integer, path parameter). It SHALL call the existing seat
reservation logic and:
- on success, redirect (HTTP 302) to the reservation confirmation page for the
  new reservation;
- on failure (seat already reserved), redirect (HTTP 302) back to the seat
  selection page for that seat's screening with `?error=1`.

#### Scenario: Reserving an available seat
- **WHEN** a browser sends `POST /seats/<seat_id>/reserve/` for an available seat
- **THEN** a confirmed reservation SHALL be created for that seat and the
  response SHALL redirect to the URL named `reservation-confirmation` for the
  new reservation's ID

#### Scenario: Reserving an already-reserved seat
- **WHEN** a browser sends `POST /seats/<seat_id>/reserve/` for a seat that
  already has a confirmed reservation
- **THEN** no new reservation SHALL be created and the response SHALL redirect
  to the seat selection page for that seat's screening with `?error=1`

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

