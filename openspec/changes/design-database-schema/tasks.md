## 1. Movie model

- [x] 1.1 Create `Movie` model with title, description, release_date, runtime_minutes, poster_image fields
- [x] 1.2 Add default ordering by release_date descending and `__str__` method
- [x] 1.3 Register Movie with Django admin

## 2. Screening model

- [x] 2.1 Create `Screening` model with FK to Movie, venue, start_time, base_price
- [x] 2.2 Add validation to reject past start times (clean method or model constraint)
- [x] 2.3 Override `save()` or use `post_save` signal to auto-generate Seat rows on creation
- [x] 2.4 Register Screening with Django admin

## 3. Seat model

- [x] 3.1 Create `Seat` model with FK to Screening, row (CharField), number (PositiveIntegerField)
- [x] 3.2 Add `unique_together` constraint on (screening, row, number)
- [x] 3.3 Add a method/property to check if seat is available (no active reservation)

## 4. Reservation model

- [x] 4.1 Create `Reservation` model with FK to Seat, booking_id (UUID), status (confirmed/cancelled), created_at
- [x] 4.2 Add unique constraint on (seat, status) filtered to status=confirmed to prevent double-booking
- [x] 4.3 Implement `reserve_seat()` service function using `select_for_update()` in an atomic transaction
- [x] 4.4 Implement `cancel_reservation()` service function
- [x] 4.5 Register Reservation with Django admin

## 5. Database migration

- [x] 5.1 Run `makemigrations` and verify migration file is correct
- [x] 5.2 Run `migrate` to apply to the development database

## 6. Tests

- [x] 6.1 Test creating a movie with validation
- [x] 6.2 Test creating a screening with seat generation
- [x] 6.3 Test concurrent seat reservation prevents double-booking
- [x] 6.4 Test reservation cancellation frees the seat
- [x] 6.5 Test available seats query excludes reserved seats
