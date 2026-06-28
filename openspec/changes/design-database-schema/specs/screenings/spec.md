## ADDED Requirements

### Requirement: Screening data model
The system SHALL store screenings linking a movie to a specific start time, venue location, and base ticket price.

#### Scenario: Create a screening
- **WHEN** an admin creates a screening for "Dune: Part Three" on 2027-11-01 at 19:00 in "Auditorium 1" with a price of $14.50
- **THEN** the screening is stored and associated with the correct movie

#### Scenario: Screening requires a movie
- **WHEN** an admin attempts to create a screening without linking it to a movie
- **THEN** the system SHALL reject the save

#### Scenario: Screening requires a future start time
- **WHEN** an admin creates a screening with a start time in the past
- **THEN** the system SHALL reject the save with a validation error

#### Scenario: List screenings for a movie
- **WHEN** querying screenings for a specific movie
- **THEN** only screenings for that movie SHALL be returned, ordered by start time ascending

### Requirement: Screening seat generation
When a screening is created, the system SHALL automatically generate seats for that screening based on a configurable row and column count.

#### Scenario: Seats created on screening save
- **WHEN** a screening is saved with venue "Auditorium 1" (config: rows 8, columns 12)
- **THEN** 96 seat records are created (rows A-H, seats 1-12 each)
