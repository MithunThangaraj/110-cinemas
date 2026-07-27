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
page listing movies and a search form. The listing SHALL be split into films
that are bookable now (those with a screening still to come) and films that are
not yet scheduled. A search SHALL cover both. It SHALL accept
an optional `q` query parameter (a title search) submitted via a **GET** form;
when `q` is provided, the list SHALL be filtered to movies whose title contains
`q` (case-insensitive).

#### Scenario: Listing movies
- **WHEN** a browser sends `GET /movies/`
- **THEN** the response SHALL be HTTP 200 with an HTML page containing the title
  of every `Movie` in the database

#### Scenario: Splitting the listing
- **WHEN** a browser sends `GET /movies/`
- **THEN** films with at least one screening in the future SHALL be listed as
  "now showing" with links to book them, and every other film SHALL be listed
  as "coming soon" with its release date and no booking links

#### Scenario: Searching movies by title
- **WHEN** a browser sends `GET /movies/?q=<term>`
- **THEN** the response SHALL be HTTP 200 listing only movies whose title
  contains `<term>` (case-insensitive)

### Requirement: Seat selection page
The system SHALL expose `GET /screenings/<screening_id>/seats/`
(name: `seat-selection`) taking a `screening_id` (integer, path parameter) and
returning an HTML page that shows every seat for that screening as a seat map,
where each available seat is a checkbox and reserved seats are shown as
unavailable. Up to 6 seats may be chosen and reserved as one booking.

The map is generated from the screening's auditorium, so its size and shape
follow the screen format (an IMAX GT house is far larger than a 4DX room).
Seats are marked by kind — standard, premium, or wheelchair space — and each
kind's price is shown, in yen.

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
chosen seats are submitted as repeated `seats` form fields. The view SHALL
ignore any submitted seat that does not belong to the screening, and SHALL
reject a submission of no seats, of more than the per-booking maximum (6), or
including a seat that is already taken.

Booking happens in two steps, distinguished by a `step` field:

- **No `step`** — the seats are accepted and the response asks who the booking
  is for (a name and email). Nothing is reserved yet.
- **`step=details`** — the submitted name and email are validated and the
  booking is created. Invalid details SHALL re-render the details step without
  reserving anything.
- **`step=seats`** — "back": the response is the seat map again with the
  submitted seats still selected, and nothing reserved.

Seats are NOT held between the two steps. If a seat is taken while the visitor
is entering their details, the booking SHALL fail and the response SHALL be the
seat map with an error, not a dead form.

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
booking reference. When the booking is still confirmed and was made in the
current session, the page SHALL also offer to cancel it; a cancelled booking
SHALL be shown as cancelled instead.

#### Scenario: Viewing a confirmation for an existing booking
- **WHEN** a browser sends `GET /bookings/<group_id>/` for a booking that exists
- **THEN** the response SHALL be HTTP 200 with an HTML page showing every seat
  in the booking, the screening details, and the total price

#### Scenario: Viewing a confirmation for an unknown booking
- **WHEN** a browser sends `GET /bookings/<group_id>/` for a `group_id` with no
  reservations
- **THEN** the response SHALL be HTTP 404

### Requirement: Live seat availability
The system SHALL expose `GET /screenings/<screening_id>/availability/`
(name: `seat-availability`), which the seat selection page polls so the map
stays current while a visitor is choosing.

The request carries a `v` parameter holding the availability digest the client
last rendered, and the visitor's current selection as repeated `seats`
parameters.

- **WHEN** the digest matches the screening's current availability, the
  response SHALL be HTTP 204 with an empty body, so the client leaves the page
  untouched. This is what keeps an idle poll from causing a visible flicker or
  taking focus from a visitor part way through choosing.
- **WHEN** availability has changed, the response SHALL be the reservation-area
  fragment re-rendered with the seats now taken marked as such, and with the
  visitor's selection preserved.
- Any selected seat that has since been taken SHALL be dropped from the
  selection, and the response SHALL say which seats went.

#### Scenario: Polling when nothing has changed
- **WHEN** the page polls with a digest matching current availability
- **THEN** the response SHALL be HTTP 204 with an empty body

#### Scenario: Polling after someone else books
- **WHEN** the page polls with a stale digest
- **THEN** the response SHALL be the reservation-area fragment showing the
  newly taken seats, with the visitor's own selection still selected

#### Scenario: A selected seat is taken by someone else
- **WHEN** the page polls with a stale digest and one of the submitted `seats`
  now has a confirmed reservation
- **THEN** that seat SHALL be dropped from the selection, the visitor's other
  seats SHALL stay selected, and the response SHALL name the seat that went

### Requirement: Cancel booking action
The system SHALL expose `POST /bookings/<group_id>/cancel/`
(name: `cancel-booking`) taking a `group_id` (UUID, path parameter). It SHALL
cancel every confirmed reservation in that booking, making the seats available
again.

The action SHALL only accept POST: a GET SHALL NOT change any state, because a
browser or crawler prefetching a link would otherwise cancel bookings.

**Access control:** only the session that made the booking may cancel it.
Booking references are UUIDs in the URL, so a request whose session does not
hold the group ID SHALL receive HTTP 404 (not 403, so that valid booking
references cannot be probed).

On success it SHALL add a success flash message and redirect (HTTP 302) to the
my-bookings page, or return an `HX-Redirect` to it for HTMX requests. If the
booking is already cancelled it SHALL add an error message instead and create
no change.

#### Scenario: Cancelling a booking made in this session
- **WHEN** a browser sends `POST /bookings/<group_id>/cancel/` for a confirmed
  booking whose group ID is in its session
- **THEN** every reservation in that booking SHALL become "cancelled", every
  seat SHALL become available for booking again, and the response SHALL
  redirect to the my-bookings page

#### Scenario: Cancelling another visitor's booking
- **WHEN** a browser sends `POST /bookings/<group_id>/cancel/` for a booking
  whose group ID is not in its session
- **THEN** the response SHALL be HTTP 404 and the booking SHALL be unchanged

#### Scenario: Cancelling with a GET request
- **WHEN** a browser sends `GET /bookings/<group_id>/cancel/`
- **THEN** the response SHALL be HTTP 405 and the booking SHALL be unchanged

#### Scenario: Cancelling an already-cancelled booking
- **WHEN** a browser cancels a booking that is already cancelled
- **THEN** no change SHALL be made and the response SHALL report that the
  booking is not active

### Requirement: My bookings page
The system SHALL expose `GET /my-bookings/` (name: `my-bookings`) that takes no
arguments and returns an HTML page listing the bookings whose group IDs are
stored in the current session, each showing all of its seats, linking to its
confirmation page, and offering to cancel it while it is still confirmed. This
lets a visitor review and release the seats they reserved during the current
visit without an account.

#### Scenario: Viewing bookings made this session
- **WHEN** a browser sends `GET /my-bookings/` after reserving one or more seats
  in the same session
- **THEN** the response SHALL be HTTP 200 with an HTML page listing those seats,
  with seats reserved together shown as a single booking

#### Scenario: Viewing bookings with an empty session
- **WHEN** a browser sends `GET /my-bookings/` without having reserved any seat
- **THEN** the response SHALL be HTTP 200 with an HTML page indicating there are
  no bookings yet

