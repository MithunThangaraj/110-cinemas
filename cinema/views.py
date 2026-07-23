from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from .forms import MovieSearchForm, ReservationForm
from .models import Movie, Reservation, Screening
from .services import reserve_seat

# Session key under which we remember the booking IDs made in the current
# visit, so a visitor can see "My Bookings" without needing an account.
SESSION_BOOKINGS_KEY = "booking_ids"


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


def seat_selection(request, screening_id):
    screening = get_object_or_404(Screening, pk=screening_id)
    return render(
        request,
        "cinema/seat_selection.html",
        {
            "screening": screening,
            "seats": screening.seats.all(),
            "form": ReservationForm(),
        },
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
    form = ReservationForm(request.POST)

    seat_id = _parse_int(request.POST.get("seat"))
    seat = screening.seats.filter(pk=seat_id).first() if seat_id else None

    context = {
        "screening": screening,
        "seats": screening.seats.all(),
        "form": form,
        "selected_seat_id": seat.id if seat else None,
    }

    if seat is None:
        context["seat_error"] = "Please choose a seat first."
    if seat is None or not form.is_valid():
        return _render_reservation_area(request, context)

    try:
        reservation = reserve_seat(
            seat.id,
            customer_name=form.cleaned_data["customer_name"],
            customer_email=form.cleaned_data["customer_email"],
        )
    except ValidationError:
        context["selected_seat_id"] = None
        context["seat_error"] = "That seat was just taken. Please choose another one."
        return _render_reservation_area(request, context)

    booking_ids = request.session.setdefault(SESSION_BOOKINGS_KEY, [])
    booking_ids.append(str(reservation.booking_id))
    request.session.modified = True

    confirmation_url = reverse("reservation-confirmation", args=[reservation.id])
    if request.htmx:
        return HttpResponseClientRedirect(confirmation_url)

    messages.success(request, f"Seat {seat.row}{seat.number} reserved.")
    return redirect(confirmation_url)


def reservation_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    return render(
        request, "cinema/reservation_confirmation.html", {"reservation": reservation}
    )


def my_bookings(request):
    booking_ids = request.session.get(SESSION_BOOKINGS_KEY, [])
    reservations = Reservation.objects.filter(booking_id__in=booking_ids)
    return render(request, "cinema/my_bookings.html", {"reservations": reservations})
