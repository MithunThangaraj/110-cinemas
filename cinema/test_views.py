import pytest
from django.urls import reverse

from .services import reserve_seat

VALID_RESERVATION = {
    "customer_name": "Ada Lovelace",
    "customer_email": "ada@example.com",
}


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

    def test_movie_search_filters_by_title(self, client, movie):
        matching = client.get(reverse("movie-list"), {"q": "dune"})
        assert movie.title.encode() in matching.content
        missing = client.get(reverse("movie-list"), {"q": "nope"})
        assert movie.title.encode() not in missing.content


@pytest.mark.django_db
class TestSeatSelection:
    def test_seat_selection_lists_seats(self, client, future_screening):
        response = client.get(reverse("seat-selection", args=[future_screening.id]))
        assert response.status_code == 200
        assert b"A1" in response.content

    def test_seat_selection_shows_reservation_form(self, client, future_screening):
        response = client.get(reverse("seat-selection", args=[future_screening.id]))
        assert response.status_code == 200
        assert b"customer_name" in response.content
        assert b"customer_email" in response.content

    def test_seat_selection_missing_screening_404s(self, client):
        response = client.get(reverse("seat-selection", args=[9999]))
        assert response.status_code == 404


def reserve_payload(seat, **overrides):
    data = {"seat": seat.id, **VALID_RESERVATION}
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestReserveSeats:
    def _url(self, screening):
        return reverse("reserve-seats", args=[screening.id])

    def test_reserve_selected_seat_redirects_to_confirmation(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        response = client.post(self._url(future_screening), reserve_payload(seat))
        seat.refresh_from_db()
        assert response.status_code == 302
        assert seat.is_available is False
        reservation = seat.reservations.get(status="confirmed")
        assert reservation.customer_name == "Ada Lovelace"
        assert reservation.customer_email == "ada@example.com"
        assert response.url == reverse(
            "reservation-confirmation", args=[reservation.id]
        )

    def test_reserve_remembers_booking_in_session(self, client, future_screening):
        seat = future_screening.seats.first()
        client.post(self._url(future_screening), reserve_payload(seat))
        reservation = seat.reservations.get(status="confirmed")
        assert str(reservation.booking_id) in client.session["booking_ids"]

    def test_reserve_without_seat_shows_error(self, client, future_screening):
        response = client.post(self._url(future_screening), VALID_RESERVATION)
        assert response.status_code == 200
        assert b"choose a seat" in response.content
        assert future_screening.seats.first().is_available is True

    def test_reserve_with_invalid_email_re_renders_without_booking(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        response = client.post(
            self._url(future_screening),
            reserve_payload(seat, customer_email="not-an-email"),
        )
        assert response.status_code == 200
        assert seat.reservations.filter(status="confirmed").count() == 0

    def test_reserve_missing_name_re_renders_without_booking(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        response = client.post(
            self._url(future_screening),
            reserve_payload(seat, customer_name=""),
        )
        assert response.status_code == 200
        assert seat.reservations.filter(status="confirmed").count() == 0

    def test_reserve_already_taken_seat_shows_error(self, client, future_screening):
        seat = future_screening.seats.first()
        reserve_seat(seat.id)
        response = client.post(self._url(future_screening), reserve_payload(seat))
        assert response.status_code == 200
        assert b"just taken" in response.content
        assert seat.reservations.filter(status="confirmed").count() == 1


@pytest.mark.django_db
class TestReserveSeatsHtmx:
    def _url(self, screening):
        return reverse("reserve-seats", args=[screening.id])

    def test_htmx_reserve_returns_client_redirect(self, client, future_screening):
        seat = future_screening.seats.first()
        response = client.post(
            self._url(future_screening),
            reserve_payload(seat),
            HTTP_HX_REQUEST="true",
        )
        seat.refresh_from_db()
        assert response.status_code == 200
        assert seat.is_available is False
        reservation = seat.reservations.get(status="confirmed")
        assert response["HX-Redirect"] == reverse(
            "reservation-confirmation", args=[reservation.id]
        )
        assert str(reservation.booking_id) in client.session["booking_ids"]

    def test_htmx_invalid_email_returns_partial_with_errors(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        response = client.post(
            self._url(future_screening),
            reserve_payload(seat, customer_email="not-an-email"),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"<html" not in response.content
        assert b"customer_email" in response.content
        assert seat.reservations.filter(status="confirmed").count() == 0

    def test_htmx_without_seat_returns_partial_error(self, client, future_screening):
        response = client.post(
            self._url(future_screening),
            VALID_RESERVATION,
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"<html" not in response.content
        assert b"choose a seat" in response.content

    def test_htmx_already_taken_seat_returns_partial(self, client, future_screening):
        seat = future_screening.seats.first()
        reserve_seat(seat.id)
        response = client.post(
            self._url(future_screening),
            reserve_payload(seat),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"just taken" in response.content
        assert seat.reservations.filter(status="confirmed").count() == 1


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


@pytest.mark.django_db
class TestMyBookings:
    def test_my_bookings_lists_seats_reserved_this_session(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            reserve_payload(seat),
        )
        response = client.get(reverse("my-bookings"))
        assert response.status_code == 200
        assert f"{seat.row}{seat.number}".encode() in response.content

    def test_my_bookings_empty_without_reservations(self, client):
        response = client.get(reverse("my-bookings"))
        assert response.status_code == 200
        assert b"no bookings" in response.content
