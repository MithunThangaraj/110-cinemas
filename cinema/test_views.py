import pytest
from django.urls import reverse

from .services import reserve_seat


@pytest.mark.django_db
class TestIndex:
    def test_index_redirects_to_movie_list(self, client):
        response = client.get(reverse("index"))
        assert response.status_code == 302
        assert response.url == reverse("movie-list")


@pytest.mark.django_db
class TestMovieList:
    def test_movie_list_shows_movies(self, client, movie):
        response = client.get(reverse("movie-list"))
        assert response.status_code == 200
        assert movie.title.encode() in response.content


@pytest.mark.django_db
class TestSeatSelection:
    def test_seat_selection_lists_seats(self, client, future_screening):
        response = client.get(reverse("seat-selection", args=[future_screening.id]))
        assert response.status_code == 200
        assert b"A1" in response.content

    def test_seat_selection_missing_screening_404s(self, client):
        response = client.get(reverse("seat-selection", args=[9999]))
        assert response.status_code == 404

    def test_seat_selection_shows_error_message(self, client, future_screening):
        response = client.get(
            reverse("seat-selection", args=[future_screening.id]), {"error": "1"}
        )
        assert response.status_code == 200
        assert b"already reserved" in response.content


@pytest.mark.django_db
class TestReserveSeatView:
    def test_reserve_available_seat_redirects_to_confirmation(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        response = client.post(reverse("reserve-seat", args=[seat.id]))
        seat.refresh_from_db()
        assert response.status_code == 302
        assert seat.is_available is False
        reservation = seat.reservations.get(status="confirmed")
        assert response.url == reverse(
            "reservation-confirmation", args=[reservation.id]
        )

    def test_reserve_already_reserved_seat_redirects_with_error(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        reserve_seat(seat.id)
        response = client.post(reverse("reserve-seat", args=[seat.id]))
        assert response.status_code == 302
        assert response.url == (
            f"{reverse('seat-selection', args=[future_screening.id])}?error=1"
        )


@pytest.mark.django_db
class TestReservationConfirmation:
    def test_confirmation_shows_booking_details(self, client, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        response = client.get(
            reverse("reservation-confirmation", args=[reservation.id])
        )
        assert response.status_code == 200
        assert str(reservation.booking_id).encode() in response.content
