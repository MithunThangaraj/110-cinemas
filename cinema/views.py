from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .models import Movie, Reservation, Screening, Seat
from .services import reserve_seat

# Session key under which we remember the booking IDs made in the current
# visit, so a visitor can see "My Bookings" without needing an account.
SESSION_BOOKINGS_KEY = "booking_ids"


def index(request):
    return redirect("movie-list")


def movie_list(request):
    movies = Movie.objects.all()
    return render(request, "cinema/movie_list.html", {"movies": movies})


def seat_selection(request, screening_id):
    screening = get_object_or_404(Screening, pk=screening_id)
    seats = screening.seats.all()
    return render(
        request,
        "cinema/seat_selection.html",
        {"screening": screening, "seats": seats},
    )


def reserve_seat_view(request, seat_id):
    try:
        reservation = reserve_seat(seat_id)
    except ValidationError:
        seat = get_object_or_404(Seat, pk=seat_id)
        messages.error(
            request, "That seat was already reserved. Please pick another one."
        )
        return redirect("seat-selection", screening_id=seat.screening_id)

    booking_ids = request.session.setdefault(SESSION_BOOKINGS_KEY, [])
    booking_ids.append(str(reservation.booking_id))
    request.session.modified = True

    messages.success(
        request, f"Seat {reservation.seat.row}{reservation.seat.number} reserved."
    )
    return redirect("reservation-confirmation", reservation_id=reservation.id)


def reservation_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    return render(
        request, "cinema/reservation_confirmation.html", {"reservation": reservation}
    )


def my_bookings(request):
    booking_ids = request.session.get(SESSION_BOOKINGS_KEY, [])
    reservations = Reservation.objects.filter(booking_id__in=booking_ids)
    return render(request, "cinema/my_bookings.html", {"reservations": reservations})
