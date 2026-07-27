import hashlib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef

from .models import Booking, BookingItem, MenuItem, Reservation, Seat

# How many seats one visitor may reserve in a single booking.
MAX_SEATS_PER_BOOKING = 6

# How many of any one menu item can go on a booking.
MAX_ITEM_QUANTITY = 10

# Session key under which a guest's bookings are remembered, so they can see
# them without an account.
SESSION_BOOKINGS_KEY = "booking_references"


def validate_selection(seat_ids):
    """Check how many seats were chosen, before anything is booked.

    Shared so the view can reject a bad selection up front rather than walking
    the visitor through the details step only to fail at the end.
    """
    if not seat_ids:
        raise ValidationError("Choose at least one seat.")
    if len(seat_ids) > MAX_SEATS_PER_BOOKING:
        raise ValidationError(
            f"You can book at most {MAX_SEATS_PER_BOOKING} seats at a time."
        )


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


def seat_rows(screening):
    """The screening's seats grouped into rows, ready to render.

    Rows differ in length once a layout tapers, so whether an aisle falls after
    a seat depends on how long its row is. Working that out here keeps the
    arithmetic out of the template.
    """
    layout = screening.auditorium.layout
    rows = {}
    for seat in seats_with_availability(screening):
        rows.setdefault(seat.row, []).append(seat)

    grouped = []
    for label, row_seats in rows.items():
        for seat in row_seats:
            seat.is_aisle = layout.is_aisle(seat.number, len(row_seats))
        grouped.append({"label": label, "seats": row_seats})
    return grouped


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


def parse_item_quantities(data, items):
    """Read requested quantities out of submitted form data.

    Returns [(item, quantity)] for anything with a sensible quantity, ignoring
    blanks, zeroes and junk rather than failing the whole booking over a stray
    value in an optional field.
    """
    chosen = []
    for item in items:
        raw = data.get(f"item_{item.id}")
        try:
            quantity = int(raw)
        except (TypeError, ValueError):
            continue
        if quantity <= 0:
            continue
        chosen.append((item, min(quantity, MAX_ITEM_QUANTITY)))
    return chosen


@transaction.atomic
def create_booking(seat_ids, customer_name="", customer_email="", items=(), user=None):
    """Reserve several seats as one booking, or none of them at all.

    `items` is [(MenuItem, quantity)] to add to the same booking. `user` is the
    signed-in member, if any: guests book without an account.

    Returns the `Booking`.
    """
    # dict.fromkeys de-duplicates while keeping the submitted order.
    seat_ids = list(dict.fromkeys(seat_ids))
    validate_selection(seat_ids)

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

    booking = Booking.objects.create(
        user=user,
        customer_name=customer_name,
        customer_email=customer_email,
        # Recorded on the booking, not recomputed later, so changing the offer
        # cannot rewrite what a past booking cost.
        discount=Booking.MEMBER_DISCOUNT if user is not None else 0,
    )

    for seat in seats:
        Reservation.objects.create(seat=seat, booking=booking)

    for item, quantity in items:
        BookingItem.objects.create(
            booking=booking,
            item=item,
            quantity=quantity,
            # Snapshot the price: the menu can change, this order cannot.
            unit_price=item.price,
        )

    return booking


def reserve_seat(seat_id, customer_name="", customer_email=""):
    """Reserve a single seat. Thin wrapper around `create_booking`."""
    booking = create_booking([seat_id], customer_name, customer_email)
    return booking.reservations.first()


@transaction.atomic
def cancel_booking(booking):
    """Cancel every confirmed seat in a booking, freeing all of them at once.

    Cancelling only changes `status`, so the partial unique constraint on
    confirmed reservations no longer applies and the seats can be booked again.

    Cancelling is booking-wide on purpose: a per-seat cancel would let a booking
    end up half-cancelled, which the confirmation page has no sensible way to
    describe.
    """
    reservations = list(
        Reservation.objects.select_for_update().filter(
            booking=booking, status=Reservation.Status.CONFIRMED
        )
    )
    if not reservations:
        raise ValidationError("That booking is not active.")

    for reservation in reservations:
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])
    return reservations


def bookings_for(request):
    """The bookings this visitor may see.

    A signed-in member sees everything they have ever booked; a guest sees only
    what this browser session made, since there is no account to tie it to.
    """
    query = Booking.objects.prefetch_related(
        "items__item",
        "reservations__seat__screening__movie",
        "reservations__seat__screening__auditorium",
    )
    if request.user.is_authenticated:
        return query.filter(user=request.user)
    references = request.session.get(SESSION_BOOKINGS_KEY, [])
    return query.filter(reference__in=references)


def may_cancel(request, booking):
    """Whether this visitor is allowed to cancel this booking.

    References are UUIDs in the URL, so without this anyone holding a link
    could release someone else's seats.
    """
    if request.user.is_authenticated and booking.user_id == request.user.id:
        return True
    return str(booking.reference) in request.session.get(SESSION_BOOKINGS_KEY, [])


def remember_booking(request, booking):
    """Let a guest find this booking again later in the same session."""
    references = request.session.setdefault(SESSION_BOOKINGS_KEY, [])
    references.append(str(booking.reference))
    request.session.modified = True


def menu_by_category():
    """Available menu items, grouped for display."""
    items = MenuItem.objects.filter(is_available=True)
    grouped = {}
    for item in items:
        grouped.setdefault(item.get_category_display(), []).append(item)
    return [{"name": name, "items": rows} for name, rows in grouped.items()]
