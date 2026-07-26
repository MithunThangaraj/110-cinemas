import hashlib
import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef

from .models import Reservation, Seat

# How many seats one visitor may reserve in a single booking.
MAX_SEATS_PER_BOOKING = 6


def seats_with_availability(screening):
    """Every seat in a screening, annotated with whether it is taken.

    `Seat.is_available` costs one query per seat. An IMAX GT house has 468 of
    them, so rendering the map that way would be 468 queries; this is one.
    """
    taken = Reservation.objects.filter(
        seat=OuterRef("pk"), status=Reservation.Status.CONFIRMED
    )
    # select_related so each seat can price itself without another query.
    return screening.seats.select_related(
        "screening", "screening__auditorium"
    ).annotate(taken=Exists(taken))


def availability_signature(screening):
    """A short digest of which seats are taken.

    Lets the seat map poll cheaply: if the digest has not moved, nothing has
    been booked and the client is told to keep what it has.
    """
    taken = (
        Reservation.objects.filter(
            seat__screening=screening, status=Reservation.Status.CONFIRMED
        )
        .order_by("seat_id")
        .values_list("seat_id", flat=True)
    )
    joined = ",".join(str(seat_id) for seat_id in taken)
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


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

    # One query for the whole selection rather than one per seat.
    if Reservation.objects.filter(
        seat_id__in=seat_ids, status=Reservation.Status.CONFIRMED
    ).exists():
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
