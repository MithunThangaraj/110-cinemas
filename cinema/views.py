from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from .forms import MovieSearchForm
from .models import Movie, Reservation, Screening
from .services import MAX_SEATS_PER_BOOKING, create_booking

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


def _reservation_context(screening, selected_seats=(), seat_error=None):
    selected_seats = list(selected_seats)
    return {
        "screening": screening,
        "seats": screening.seats.all(),
        "selected_seats": selected_seats,
        "selected_seat_ids": [seat.id for seat in selected_seats],
        "max_seats": MAX_SEATS_PER_BOOKING,
        "seat_error": seat_error,
    }


def seat_selection(request, screening_id):
    screening = get_object_or_404(Screening, pk=screening_id)
    return render(
        request,
        "cinema/seat_selection.html",
        _reservation_context(screening),
    )


def _render_reservation_area(request, context):
    # HTMX swaps only the reservation area; a normal request gets the full page.
    template = (
        "cinema/_reservation_area.html"
        if request.htmx
        else "cinema/seat_selection.html"
    )
    return render(request, template, context)


def reserve_seats(request, screening_id):
    screening = get_object_or_404(Screening, pk=screening_id)

    seat_ids = [_parse_int(value) for value in request.POST.getlist("seats")]
    # Only seats belonging to this screening may be booked from this page.
    seats = list(screening.seats.filter(pk__in=[i for i in seat_ids if i]))

    if not seats:
        return _render_reservation_area(
            request,
            _reservation_context(screening, seat_error="Please choose a seat first."),
        )

    try:
        reservations = create_booking([seat.id for seat in seats])
    except ValidationError as error:
        return _render_reservation_area(
            request,
            _reservation_context(
                screening,
                selected_seats=seats,
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

    messages.success(request, f"Reserved {len(reservations)} seat(s).")
    return redirect(confirmation_url)


def booking_confirmation(request, group_id):
    reservations = list(
        Reservation.objects.filter(group_id=group_id)
        .select_related("seat", "seat__screening", "seat__screening__movie")
        .order_by("seat__row", "seat__number")
    )
    if not reservations:
        raise Http404("No booking with that reference.")

    screening = reservations[0].seat.screening
    return render(
        request,
        "cinema/booking_confirmation.html",
        {
            "group_id": group_id,
            "reservations": reservations,
            "screening": screening,
            "seats": [reservation.seat for reservation in reservations],
            "total": screening.base_price * len(reservations),
        },
    )


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
                "status": reservation.status,
                "seats": [],
            },
        )
        booking["seats"].append(reservation.seat)
    return sorted(bookings.values(), key=lambda b: b["created_at"], reverse=True)


def my_bookings(request):
    group_ids = request.session.get(SESSION_BOOKINGS_KEY, [])
    reservations = (
        Reservation.objects.filter(group_id__in=group_ids)
        .select_related("seat", "seat__screening", "seat__screening__movie")
        .order_by("seat__row", "seat__number")
    )
    return render(
        request,
        "cinema/my_bookings.html",
        {"bookings": _group_into_bookings(reservations)},
    )
