# screenings Specification

## Purpose
TBD - created by archiving change design-database-schema. Update Purpose after archive.
## Requirements
### Requirement: Screening data model
The system SHALL store screenings linking a movie to a specific start time, an
auditorium, and a base ticket price in yen (a whole number: the currency has no
minor unit).

An `Auditorium` is a physical screen with a format — standard, IMAX GT, Dolby
Cinema, or 4DX — and a surcharge in yen. The format decides the room's seat
layout, so auditoriums of different formats are different sizes and shapes.

The price of one seat SHALL be the screening's base price, plus the
auditorium's surcharge, plus the seat kind's surcharge.

#### Scenario: Create a screening
- **WHEN** an admin creates a screening for a movie on 2027-11-01 at 19:00 in the "IMAX GT" auditorium with a base price of ¥2,000
- **THEN** the screening is stored and associated with the correct movie

#### Scenario: Screening requires a movie
- **WHEN** an admin attempts to create a screening without linking it to a movie
- **THEN** the system SHALL reject the save

#### Scenario: Screening requires a future start time
- **WHEN** an admin creates a screening with a start time in the past
- **THEN** the system SHALL reject the save with a validation error

#### Scenario: Pricing follows the auditorium and the seat
- **WHEN** a screening with a base price of ¥2,000 runs in an IMAX GT
  auditorium with a ¥1,000 surcharge
- **THEN** a standard seat SHALL cost ¥3,000 and a premium seat ¥3,500

#### Scenario: List screenings for a movie
- **WHEN** querying screenings for a specific movie
- **THEN** only screenings for that movie SHALL be returned, ordered by start time ascending

### Requirement: Screening seat generation
When a screening is created, the system SHALL automatically generate its seats
from its auditorium's layout. Each seat SHALL be assigned a kind: standard,
premium (the centre block), or wheelchair space.

Every layout SHALL include wheelchair spaces, and a wheelchair space SHALL
never be priced at the premium rate even when it sits inside the premium block.

#### Scenario: Seats created on screening save
- **WHEN** a screening is saved in a standard auditorium (10 rows x 18 seats)
- **THEN** 180 seat records are created (rows A-J, seats 1-18 each)

#### Scenario: Larger formats get larger rooms
- **WHEN** a screening is saved in an IMAX GT auditorium
- **THEN** 468 seat records are created, more than any other format, and a 4DX
  auditorium SHALL produce the fewest

#### Scenario: Every room has accessible seating
- **WHEN** a screening is saved in any auditorium
- **THEN** at least one of its seats SHALL be a wheelchair space

