from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Movie, Reservation, Screening, Seat
from .services import reserve_seat


def index(request):
    return redirect("movie-list")


def movie_list(request):
    movies = Movie.objects.all()
    return render(request, "cinema/movie_list.html", {"movies": movies})


def seat_selection(request, screening_id):
    screening = get_object_or_404(Screening, pk=screening_id)
    seats = screening.seats.all()
    show_error = request.GET.get("error") == "1"
    return render(
        request,
        "cinema/seat_selection.html",
        {"screening": screening, "seats": seats, "show_error": show_error},
    )


def reserve_seat_view(request, seat_id):
    try:
        reservation = reserve_seat(seat_id)
    except ValidationError:
        seat = get_object_or_404(Seat, pk=seat_id)
        seat_selection_url = reverse("seat-selection", args=[seat.screening_id])
        return redirect(f"{seat_selection_url}?error=1")
    return redirect("reservation-confirmation", reservation_id=reservation.id)


def reservation_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    return render(
        request, "cinema/reservation_confirmation.html", {"reservation": reservation}
    )
