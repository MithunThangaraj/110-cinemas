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
returning an HTML page that shows every seat for that screening as a seat map,
where each available seat is a checkbox and reserved seats are shown as
unavailable. Up to 6 seats may be chosen and reserved as one booking; no
customer details are collected.

#### Scenario: Viewing seats for an existing screening
- **WHEN** a browser sends `GET /screenings/<screening_id>/seats/` for a screening
  that exists
- **THEN** the response SHALL be HTTP 200 with an HTML page listing all of that
  screening's seats, marking each as available or reserved, offering the
  available ones as checkboxes, and stating the maximum number of seats that
  may be booked at once

#### Scenario: Viewing seats for a non-existent screening
- **WHEN** a browser sends `GET /screenings/<screening_id>/seats/` for a
  `screening_id` that does not exist
- **THEN** the response SHALL be HTTP 404

### Requirement: Reserve seats action
The system SHALL expose `POST /screenings/<screening_id>/reserve/`
(name: `reserve-seats`) taking a `screening_id` (integer, path parameter). The
chosen seats are submitted as repeated `seats` form fields. No customer details
are collected. The view SHALL ignore any submitted seat that does not belong to
the screening, and SHALL reject a submission of no seats or of more than the
per-booking maximum (6).

Seats reserved together form one booking: the reservations created SHALL share
a `group_id`, and the booking SHALL be all-or-nothing — if any chosen seat is
already taken, none of them are reserved.

Behavior depends on whether the request carries the `HX-Request` header:

**Non-HTMX requests:**
- On success, it SHALL reserve every chosen seat, store the booking's group ID
  in the session (so it appears in "My Bookings"), add a success flash message,
  and redirect (HTTP 302) to the booking confirmation page.
- On any validation problem — no seat chosen, too many seats, or one of the
  seats was already taken — it SHALL re-render the full seat selection page
  (HTTP 200) with an error message and create no reservation.

**HTMX requests** (`HX-Request` header present):
- On success, it SHALL reserve the seats, store the group ID in the session,
  and return a client redirect (an `HX-Redirect` response) to the booking
  confirmation page.
- On any validation problem, it SHALL return only the reservation-area HTML
  fragment (HTTP 200) re-rendered with an error message, the still-valid seats
  kept selected, and no reservation, which the client swaps in place without a
  full page reload.

#### Scenario: Reserving chosen seats (non-HTMX)
- **WHEN** a browser sends a valid `POST /screenings/<id>/reserve/` with one or
  more `seats` fields for available seats, without an `HX-Request` header
- **THEN** a confirmed reservation SHALL be created for each seat, all sharing
  one `group_id`, that group ID SHALL be stored in the session, and the
  response SHALL redirect to the URL named `booking-confirmation`

#### Scenario: Reserving chosen seats (HTMX)
- **WHEN** a browser sends the same valid request with an `HX-Request` header
- **THEN** the reservations SHALL be created and the response SHALL be an
  `HX-Redirect` to the booking confirmation page

#### Scenario: Submitting without choosing a seat
- **WHEN** a browser sends `POST /screenings/<id>/reserve/` with no `seats`
  field, or only with seats belonging to another screening
- **THEN** no reservation SHALL be created and the response SHALL show an error
  asking the visitor to choose a seat (a full page for non-HTMX, the
  reservation-area fragment for HTMX)

#### Scenario: Submitting more seats than the limit
- **WHEN** a browser sends `POST /screenings/<id>/reserve/` with more than 6
  `seats` fields
- **THEN** no reservation SHALL be created and the response SHALL show an error
  stating the maximum

#### Scenario: Reserving seats when one was just taken
- **WHEN** a browser sends a valid `POST /screenings/<id>/reserve/` where at
  least one chosen seat already has a confirmed reservation
- **THEN** no reservation SHALL be created for any of the chosen seats and the
  response SHALL show an error, with the seat map reflecting that the seat is
  now reserved

### Requirement: Booking confirmation page
The system SHALL expose `GET /bookings/<group_id>/`
(name: `booking-confirmation`) taking a `group_id` (UUID, path parameter) and
returning an HTML page showing the booking's seats, screening, total price, and
booking reference.

#### Scenario: Viewing a confirmation for an existing booking
- **WHEN** a browser sends `GET /bookings/<group_id>/` for a booking that exists
- **THEN** the response SHALL be HTTP 200 with an HTML page showing every seat
  in the booking, the screening details, and the total price

#### Scenario: Viewing a confirmation for an unknown booking
- **WHEN** a browser sends `GET /bookings/<group_id>/` for a `group_id` with no
  reservations
- **THEN** the response SHALL be HTTP 404

### Requirement: My bookings page
The system SHALL expose `GET /my-bookings/` (name: `my-bookings`) that takes no
arguments and returns an HTML page listing the bookings whose group IDs are
stored in the current session, each showing all of its seats and linking to its
confirmation page. This lets a visitor review the seats they reserved during the
current visit without an account.

#### Scenario: Viewing bookings made this session
- **WHEN** a browser sends `GET /my-bookings/` after reserving one or more seats
  in the same session
- **THEN** the response SHALL be HTTP 200 with an HTML page listing those seats,
  with seats reserved together shown as a single booking

#### Scenario: Viewing bookings with an empty session
- **WHEN** a browser sends `GET /my-bookings/` without having reserved any seat
- **THEN** the response SHALL be HTTP 200 with an HTML page indicating there are
  no bookings yet

