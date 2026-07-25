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


def cancel_reservation(reservation_id):
    reservation = Reservation.objects.get(pk=reservation_id)
    if reservation.status == "cancelled":
        raise ValidationError("Reservation is already cancelled.")
    reservation.status = "cancelled"
    reservation.save(update_fields=["status"])
    return reservation
