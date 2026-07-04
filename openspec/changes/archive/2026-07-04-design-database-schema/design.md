## Context

The app is a Django 6 + HTMX project with no models yet. The cinema `cinema/` app exists as a scaffold (settings, URLs). We need a database schema for movies, screenings, seats, and reservations. PostgreSQL is the assumed production database; SQLite is used in development.

## Goals / Non-Goals

**Goals:**
- Define Django models that capture movies, screenings, seats, and reservations
- Enforce uniqueness constraints to prevent double-booking at the database level
- Make seat layout configurable per screening (different cinemas have different row/seat counts)
- Allow admin users to manage all data via Django admin

**Non-Goals:**
- Authentication or user accounts (out of scope for this change)
- Payment processing or ticket pricing tiers
- Complex seat layouts (e.g., wheelchair spaces, VIP rows)

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Seat model scoped to screening, not global | `Seat` has a FK to `Screening` | Different screenings can have different layouts (e.g., a premiere with reserved seating vs. a regular showing); avoids a separate Auditorium model for now |
| Seat PK as composite (screening + row + number) | Use auto-increment PK with `unique_together` constraint | Simpler Django ORM support; composite PKs are cumbersome in Django |
| Reservation links a single seat + screening | `Reservation` has FK to `Seat` | One row per reserved seat; a multi-seat booking is multiple Reservation rows sharing a `booking_id` UUID |
| Optimistic locking for seat availability | `select_for_update()` in a transaction | Prevents double-booking under concurrent requests without external locking; uses Django's built-in row-level locking |
| Price stored on `Screening`, not `Movie` | `DecimalField` on Screening | Different screenings of the same movie can have different prices (matinee vs. evening) |
| Timestamp fields on Reservation | `created_at` + `status` (confirmed/cancelled) | Enables cancellation flow and audit trail |

## Risks / Trade-offs

- **[Concurrency]** Two users selecting the same seat at the same moment → mitigated by `select_for_update()` within an atomic transaction. A unique constraint on `(seat_id, status)` for active reservations adds a second safety layer.
- **[Migration overhead]** Adding an `Auditorium` model later would require a schema migration and updating Screening → Seat relationships. Acceptable for now — the flat Seat-per-Screening model is simpler and sufficient for v1.
- **[No user model]** Without authentication, reservations cannot be tied to a user. Left for a future auth change.
