from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from .forms import MovieSearchForm, ReservationForm
from .models import MenuItem, Movie, Reservation, Screening
from .services import (
    MAX_ITEM_QUANTITY,
    MAX_SEATS_PER_BOOKING,
    availability_signature,
    booking_extras,
    cancel_booking,
    create_booking,
    menu_by_category,
    parse_item_quantities,
    seat_rows,
    seats_with_availability,
    validate_selection,
)

# Session key under which we remember the bookings made in the current visit,
# so a visitor can see "My Bookings" without needing an account.
SESSION_BOOKINGS_KEY = "booking_group_ids"


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def index(request):
    return redirect("movie-list")


def movie_list(request):
    form = MovieSearchForm(request.GET)
    movies = Movie.objects.all()
    if form.is_valid() and form.cleaned_data["q"]:
        movies = movies.filter(title__icontains=form.cleaned_data["q"])
    return render(request, "cinema/movie_list.html", {"movies": movies, "form": form})


def menu(request):
    return render(request, "cinema/menu.html", {"menu": menu_by_category()})


def _reservation_context(screening, selected_seats=(), seat_error=None):
    selected_seats = list(selected_seats)
    return {
        "screening": screening,
        "seat_rows": seat_rows(screening),
        "layout": screening.auditorium.layout,
        "selected_seats": selected_seats,
        "selected_seat_ids": [seat.id for seat in selected_seats],
        "selected_total": sum(seat.price for seat in selected_seats),
        "max_seats": MAX_SEATS_PER_BOOKING,
        "seat_error": seat_error,
        # Lets the seat map poll for changes without re-rendering when nothing
        # has been booked since this page was built.
        "availability": availability_signature(screening),
    }


def _screening_or_404(screening_id):
    return get_object_or_404(
        Screening.objects.select_related("movie", "auditorium"), pk=screening_id
    )


def seat_selection(request, screening_id):
    screening = _screening_or_404(screening_id)
    return render(
        request,
        "cinema/seat_selection.html",
        _reservation_context(screening),
    )


def seat_availability(request, screening_id):
    """Poll target for the seat map.

    Returns 204 when nothing has been booked since the client's last look, so
    HTMX leaves the DOM alone — no flicker, and no focus stolen from a visitor
    who is part way through choosing.
    """
    screening = _screening_or_404(screening_id)
    if request.GET.get("v") == availability_signature(screening):
        return HttpResponse(status=204)

    # Keep whatever the visitor had chosen, minus anything just taken.
    chosen_ids = [_parse_int(value) for value in request.GET.getlist("seats")]
    chosen = list(seats_with_availability(screening).filter(pk__in=chosen_ids))
    still_free = [seat for seat in chosen if not seat.taken]

    seat_error = None
    if len(still_free) < len(chosen):
        lost = sorted(seat.label for seat in chosen if seat.taken)
        seat_error = (
            f"Someone just booked {', '.join(lost)}. "
            "Your other seats are still selected."
        )

    return render(
        request,
        "cinema/_reservation_area.html",
        _reservation_context(screening, still_free, seat_error),
    )


def _render_reservation_area(request, context):
    # HTMX swaps only the reservation area; a normal request gets the full page.
    template = (
        "cinema/_reservation_area.html"
        if request.htmx
        else "cinema/seat_selection.html"
    )
    return render(request, template, context)


def _render_details_step(request, screening, seats, form, chosen_items=()):
    """The step that asks who the booking is for, and offers the menu."""
    quantities = {item.id: quantity for item, quantity in chosen_items}
    menu = menu_by_category()
    for group in menu:
        for item in group["items"]:
            item.chosen_quantity = quantities.get(item.id, 0)

    seats_total = sum(seat.price for seat in seats)
    extras_total = sum(item.price * quantity for item, quantity in chosen_items)
    context = {
        "screening": screening,
        "selected_seats": seats,
        "selected_total": seats_total,
        "extras_total": extras_total,
        "grand_total": seats_total + extras_total,
        "menu": menu,
        "max_item_quantity": MAX_ITEM_QUANTITY,
        "form": form,
    }
    template = (
        "cinema/_details_step.html" if request.htmx else "cinema/booking_details.html"
    )
    return render(request, template, context)


def reserve_seats(request, screening_id):
    """Choose seats, then say who the booking is for, then book.

    One view handles both steps so the chosen seats travel with the form rather
    than being parked in the session, where they would go stale.
    """
    screening = _screening_or_404(screening_id)

    seat_ids = [_parse_int(value) for value in request.POST.getlist("seats")]
    # Only seats belonging to this screening may be booked from this page.
    seats = list(
        seats_with_availability(screening).filter(pk__in=[i for i in seat_ids if i])
    )

    if not seats:
        return _render_reservation_area(
            request,
            _reservation_context(screening, seat_error="Please choose a seat first."),
        )

    # Check the selection before walking the visitor through the details step
    # only to fail at the end.
    try:
        validate_selection([seat.id for seat in seats])
    except ValidationError as error:
        return _render_reservation_area(
            request,
            _reservation_context(screening, seats, seat_error=error.messages[0]),
        )

    if any(seat.taken for seat in seats):
        return _render_reservation_area(
            request,
            _reservation_context(
                screening,
                selected_seats=[seat for seat in seats if not seat.taken],
                seat_error="Some of those seats have already been reserved.",
            ),
        )

    step = request.POST.get("step")

    if step == "seats":
        # "Back" from the details step: return to the map, selection intact.
        return _render_reservation_area(
            request, _reservation_context(screening, selected_seats=seats)
        )

    available_items = list(MenuItem.objects.filter(is_available=True))
    chosen_items = parse_item_quantities(request.POST, available_items)

    if step != "details":
        # Seats chosen; ask who they are for and offer the menu.
        return _render_details_step(
            request, screening, seats, ReservationForm(), chosen_items
        )

    form = ReservationForm(request.POST)
    if not form.is_valid():
        return _render_details_step(request, screening, seats, form, chosen_items)

    try:
        reservations = create_booking(
            [seat.id for seat in seats],
            customer_name=form.cleaned_data["customer_name"],
            customer_email=form.cleaned_data["customer_email"],
            items=chosen_items,
        )
    except ValidationError as error:
        # Seats are not held while the visitor types, so one may have gone.
        # Send them back to the map rather than leaving them on a dead form.
        return _render_reservation_area(
            request,
            _reservation_context(
                screening,
                selected_seats=[seat for seat in seats if not seat.taken],
                seat_error=error.messages[0],
            ),
        )

    group_id = str(reservations[0].group_id)
    group_ids = request.session.setdefault(SESSION_BOOKINGS_KEY, [])
    group_ids.append(group_id)
    request.session.modified = True

    confirmation_url = reverse("booking-confirmation", args=[group_id])
    if request.htmx:
        return HttpResponseClientRedirect(confirmation_url)

    count = len(reservations)
    messages.success(request, f"Reserved {count} seat{'' if count == 1 else 's'}.")
    return redirect(confirmation_url)


def _booking_status(reservations):
    """A booking counts as confirmed while any of its seats still is.

    Taking the status of one reservation would mislabel a booking that was only
    partly cancelled (which the admin can do), hiding the cancel control while
    seats were still sold.
    """
    if any(r.status == Reservation.Status.CONFIRMED for r in reservations):
        return Reservation.Status.CONFIRMED
    return Reservation.Status.CANCELLED


def _booked_in_this_session(request, group_id):
    """Whether this visitor made the booking.

    Booking references are UUIDs in the URL, so without this check anyone who
    got hold of a link could cancel someone else's seats.
    """
    return str(group_id) in request.session.get(SESSION_BOOKINGS_KEY, [])


def booking_confirmation(request, group_id):
    reservations = list(
        Reservation.objects.filter(group_id=group_id)
        .select_related(
            "seat",
            "seat__screening",
            "seat__screening__movie",
            "seat__screening__auditorium",
        )
        .order_by("seat__row", "seat__number")
    )
    if not reservations:
        raise Http404("No booking with that reference.")

    screening = reservations[0].seat.screening
    status = _booking_status(reservations)
    extras, extras_total = booking_extras(group_id)
    seats_total = sum(reservation.seat.price for reservation in reservations)
    return render(
        request,
        "cinema/booking_confirmation.html",
        {
            "group_id": group_id,
            "reservations": reservations,
            "screening": screening,
            "seats": [reservation.seat for reservation in reservations],
            "total": seats_total,
            "extras": extras,
            "extras_total": extras_total,
            "grand_total": seats_total + extras_total,
            "booked_by": reservations[0].customer_name,
            "booked_email": reservations[0].customer_email,
            "status": status,
            "can_cancel": (
                status == "confirmed" and _booked_in_this_session(request, group_id)
            ),
        },
    )


@require_POST
def cancel_booking_view(request, group_id):
    # 404 rather than 403: a visitor should not be able to probe which booking
    # references exist.
    if not _booked_in_this_session(request, group_id):
        raise Http404("No booking with that reference.")

    try:
        reservations = cancel_booking(group_id)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        count = len(reservations)
        messages.success(
            request,
            f"Booking cancelled. {count} seat{'' if count == 1 else 's'} "
            f"{'is' if count == 1 else 'are'} available again.",
        )

    url = reverse("my-bookings")
    if request.htmx:
        return HttpResponseClientRedirect(url)
    return redirect(url)


def _group_into_bookings(reservations):
    """Collapse per-seat reservations into one entry per booking."""
    bookings = {}
    for reservation in reservations:
        booking = bookings.setdefault(
            reservation.group_id,
            {
                "group_id": reservation.group_id,
                "screening": reservation.seat.screening,
                "created_at": reservation.created_at,
                "reservations": [],
                "seats": [],
            },
        )
        booking["reservations"].append(reservation)
        booking["seats"].append(reservation.seat)

    for booking in bookings.values():
        booking["status"] = _booking_status(booking["reservations"])
    return sorted(bookings.values(), key=lambda b: b["created_at"], reverse=True)


def my_bookings(request):
    group_ids = request.session.get(SESSION_BOOKINGS_KEY, [])
    reservations = (
        Reservation.objects.filter(group_id__in=group_ids)
        .select_related(
            "seat",
            "seat__screening",
            "seat__screening__movie",
            "seat__screening__auditorium",
        )
        .order_by("seat__row", "seat__number")
    )
    return render(
        request,
        "cinema/my_bookings.html",
        {"bookings": _group_into_bookings(reservations)},
    )
