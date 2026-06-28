from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Reservation, Seat


@transaction.atomic
def reserve_seat(seat_id):
    seat = Seat.objects.select_for_update().get(pk=seat_id)

    if not seat.is_available:
        raise ValidationError("Seat is already reserved.")

    return Reservation.objects.create(seat=seat)


def cancel_reservation(reservation_id):
    reservation = Reservation.objects.get(pk=reservation_id)
    if reservation.status == "cancelled":
        raise ValidationError("Reservation is already cancelled.")
    reservation.status = "cancelled"
    reservation.save(update_fields=["status"])
    return reservation
