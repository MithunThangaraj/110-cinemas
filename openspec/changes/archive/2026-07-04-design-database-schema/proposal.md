## Why

The app currently has no data models — no way to store movies, screenings, seats, or reservations. Without a database schema, the core booking functionality cannot exist. This change defines the foundational data layer so the team can build views, forms, and booking logic on top.

## What Changes

- Create four Django models: `Movie`, `Screening`, `Seat`, and `Reservation`
- Define relationships: screenings reference a movie, seats belong to a screening, reservations link a seat to a screening
- Add constraints to prevent double-booking and ensure data integrity
- Register models with Django admin for data management
- Create initial database migration

## Capabilities

### New Capabilities
- `movies-catalog`: Movie data model — title, description, release date, runtime, poster image
- `screenings`: Screening data model — which movie, venue location, start time, base price
- `seat-reservations`: Seat and reservation models — seat grid per screening, booking state, concurrent-booking-safe reservation logic

### Modified Capabilities

None — this is the first spec.

## Impact

- `cinema/models.py` — new models and business logic
- `cinema/admin.py` — admin registration for all models
- A new migration file will be generated
- All future features (views, HTMX partials, booking flow) depend on this schema
