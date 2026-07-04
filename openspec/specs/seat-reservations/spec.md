# seat-reservations Specification

## Purpose
TBD - created by archiving change design-database-schema. Update Purpose after archive.
## Requirements
### Requirement: Seat data model
The system SHALL store individual seats for each screening, identified by row label and seat number.

#### Scenario: Seat has a unique identifier within a screening
- **WHEN** two seats in the same screening have the same row and number
- **THEN** the system SHALL reject the duplicate with a database integrity error

#### Scenario: Seat availability query
- **WHEN** querying seats for a screening
- **THEN** each seat SHALL indicate whether it is available or reserved

### Requirement: Reservation data model
The system SHALL store reservations linking a seat to a screening with a status (confirmed or cancelled), a unique booking identifier, and a timestamp.

#### Scenario: Create a reservation
- **WHEN** a user reserves seat A1 for "Dune: Part Three" screening on 2027-11-01 at 19:00
- **THEN** a reservation record is created with status "confirmed" and a unique booking ID

#### Scenario: Cancel a reservation
- **WHEN** a user cancels reservation for seat A1
- **THEN** the reservation status SHALL change to "cancelled" and the seat SHALL become available again

### Requirement: Concurrent booking safety
The system SHALL prevent double-booking of the same seat under concurrent requests.

#### Scenario: Two users book the same seat simultaneously
- **WHEN** two concurrent reservation requests target the same seat at the same screening
- **THEN** exactly one reservation SHALL succeed and the other SHALL fail with a conflict error

#### Scenario: Seat remains available after a cancelled reservation
- **WHEN** a cancelled reservation exists for seat A1
- **THEN** a new reservation for seat A1 SHALL succeed

### Requirement: List available seats for a screening
The system SHALL provide a query returning only unreserved seats for a given screening.

#### Scenario: Available seats excludes reserved
- **WHEN** querying available seats for a screening where seat A1 is reserved
- **THEN** seat A1 SHALL NOT appear in the results

