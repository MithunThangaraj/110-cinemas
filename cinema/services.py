import uuid

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Reservation, Seat

# How many seats one visitor may reserve in a single booking.
MAX_SEATS_PER_BOOKING = 6


@transaction.atomic
def create_booking(seat_ids, customer_name="", customer_email=""):
    """Reserve several seats as one booking, or none of them at all.

    Returns the created reservations, which all share a `group_id`.
    """
    # dict.fromkeys de-duplicates while keeping the submitted order.
    seat_ids = list(dict.fromkeys(seat_ids))

    if not seat_ids:
        raise ValidationError("Choose at least one seat.")
    if len(seat_ids) > MAX_SEATS_PER_BOOKING:
        raise ValidationError(
            f"You can book at most {MAX_SEATS_PER_BOOKING} seats at a time."
        )

    # Lock every seat before checking availability, so two visitors booking at
    # the same time cannot both see the same seat as free. Ordering by primary
    # key keeps concurrent bookings from deadlocking against each other.
    #
    # Note: SQLite ignores select_for_update(), so on the current deployment the
    # backstop against a double booking is the partial UniqueConstraint on
    # confirmed reservations, not this lock. The lock matters on Postgres.
    seats = list(
        Seat.objects.select_for_update().filter(pk__in=seat_ids).order_by("pk")
    )
    if len(seats) != len(seat_ids):
        raise ValidationError("Some of those seats no longer exist.")

    if any(not seat.is_available for seat in seats):
        raise ValidationError("Some of those seats have already been reserved.")

    group_id = uuid.uuid4()
    return [
        Reservation.objects.create(
            seat=seat,
            group_id=group_id,
            customer_name=customer_name,
            customer_email=customer_email,
        )
        for seat in seats
    ]


def reserve_seat(seat_id, customer_name="", customer_email=""):
    """Reserve a single seat. Thin wrapper around `create_booking`."""
    return create_booking([seat_id], customer_name, customer_email)[0]


@transaction.atomic
def cancel_booking(group_id):
    """Cancel every confirmed seat in a booking, freeing all of them at once.

    Cancelling only changes `status`, so the partial unique constraint on
    confirmed reservations no longer applies and the seats can be booked again.

    Cancelling is booking-wide on purpose: a per-seat cancel would let a booking
    end up half-cancelled, which the confirmation page has no sensible way to
    describe.
    """
    reservations = list(
        Reservation.objects.select_for_update().filter(
            group_id=group_id, status=Reservation.Status.CONFIRMED
        )
    )
    if not reservations:
        raise ValidationError("That booking is not active.")

    for reservation in reservations:
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])
    return reservations
