# movies-catalog Specification

## Purpose
TBD - created by archiving change design-database-schema. Update Purpose after archive.
## Requirements
### Requirement: Movie data model
The system SHALL store movies with title, description, release date, runtime (minutes), and an optional poster image.

#### Scenario: Create a movie
- **WHEN** an admin creates a movie with title "Dune: Part Three", release date 2027-10-15, runtime 165 minutes
- **THEN** the movie is stored and retrievable by its ID

#### Scenario: Movie has required fields
- **WHEN** an admin attempts to create a movie without a title
- **THEN** the system SHALL reject the save with a validation error

#### Scenario: Movie listing ordered by release date
- **WHEN** querying all movies
- **THEN** they SHALL be ordered by release date descending by default

