import pytest
from django.test import Client
from django.urls import reverse

from .services import MAX_SEATS_PER_BOOKING, reserve_seat


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

    def test_seat_selection_offers_seat_checkboxes(self, client, future_screening):
        response = client.get(reverse("seat-selection", args=[future_screening.id]))
        assert response.status_code == 200
        assert b'name="seats"' in response.content
        assert b'type="checkbox"' in response.content

    def test_seat_selection_states_the_seat_limit(self, client, future_screening):
        response = client.get(reverse("seat-selection", args=[future_screening.id]))
        assert str(MAX_SEATS_PER_BOOKING).encode() in response.content

    def test_seat_selection_missing_screening_404s(self, client):
        response = client.get(reverse("seat-selection", args=[9999]))
        assert response.status_code == 404


@pytest.mark.django_db
class TestReserveSeats:
    def _url(self, screening):
        return reverse("reserve-seats", args=[screening.id])

    def test_reserve_one_seat_redirects_to_confirmation(self, client, future_screening):
        seat = future_screening.seats.first()
        response = client.post(self._url(future_screening), {"seats": [seat.id]})
        seat.refresh_from_db()
        assert response.status_code == 302
        assert seat.is_available is False
        reservation = seat.reservations.get(status="confirmed")
        assert response.url == reverse(
            "booking-confirmation", args=[reservation.group_id]
        )

    def test_reserve_several_seats_creates_one_booking(self, client, future_screening):
        seats = list(future_screening.seats.all()[:4])
        response = client.post(
            self._url(future_screening), {"seats": [seat.id for seat in seats]}
        )
        assert response.status_code == 302
        reservations = [seat.reservations.get(status="confirmed") for seat in seats]
        assert len({r.group_id for r in reservations}) == 1

    def test_reserve_at_the_limit_is_allowed(self, client, future_screening):
        seats = list(future_screening.seats.all()[:MAX_SEATS_PER_BOOKING])
        client.post(self._url(future_screening), {"seats": [seat.id for seat in seats]})
        assert all(seat.is_available is False for seat in seats)

    def test_reserve_over_the_limit_books_nothing(self, client, future_screening):
        seats = list(future_screening.seats.all()[: MAX_SEATS_PER_BOOKING + 1])
        response = client.post(
            self._url(future_screening), {"seats": [seat.id for seat in seats]}
        )
        assert response.status_code == 200
        assert b"at most" in response.content
        assert all(seat.is_available is True for seat in seats)

    def test_reserve_remembers_booking_in_session(self, client, future_screening):
        seat = future_screening.seats.first()
        client.post(self._url(future_screening), {"seats": [seat.id]})
        reservation = seat.reservations.get(status="confirmed")
        assert str(reservation.group_id) in client.session["booking_group_ids"]

    def test_reserve_without_seat_shows_error(self, client, future_screening):
        response = client.post(self._url(future_screening), {})
        assert response.status_code == 200
        assert b"choose a seat" in response.content
        assert future_screening.seats.first().is_available is True

    def test_seat_from_another_screening_is_ignored(
        self, client, future_screening, movie
    ):
        from datetime import timedelta

        from django.utils import timezone

        from .models import Screening

        other = Screening.objects.create(
            movie=movie,
            venue="Other",
            start_time=timezone.now() + timedelta(days=5),
            base_price="10.00",
        )
        foreign_seat = other.seats.first()
        response = client.post(
            self._url(future_screening), {"seats": [foreign_seat.id]}
        )
        assert response.status_code == 200
        assert b"choose a seat" in response.content
        assert foreign_seat.is_available is True

    def test_reserve_already_taken_seat_books_nothing(self, client, future_screening):
        seats = list(future_screening.seats.all()[:3])
        reserve_seat(seats[-1].id)
        response = client.post(
            self._url(future_screening), {"seats": [seat.id for seat in seats]}
        )
        assert response.status_code == 200
        assert b"already been reserved" in response.content
        # The seats that were free must stay free: a booking is all or nothing.
        assert seats[0].is_available is True
        assert seats[1].is_available is True


@pytest.mark.django_db
class TestReserveSeatsHtmx:
    def _url(self, screening):
        return reverse("reserve-seats", args=[screening.id])

    def test_htmx_reserve_returns_client_redirect(self, client, future_screening):
        seats = list(future_screening.seats.all()[:2])
        response = client.post(
            self._url(future_screening),
            {"seats": [seat.id for seat in seats]},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        reservation = seats[0].reservations.get(status="confirmed")
        assert response["HX-Redirect"] == reverse(
            "booking-confirmation", args=[reservation.group_id]
        )
        assert str(reservation.group_id) in client.session["booking_group_ids"]

    def test_htmx_without_seat_returns_partial_error(self, client, future_screening):
        response = client.post(self._url(future_screening), {}, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert b"<html" not in response.content
        assert b"choose a seat" in response.content

    def test_htmx_over_the_limit_returns_partial(self, client, future_screening):
        seats = list(future_screening.seats.all()[: MAX_SEATS_PER_BOOKING + 1])
        response = client.post(
            self._url(future_screening),
            {"seats": [seat.id for seat in seats]},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"<html" not in response.content
        assert b"at most" in response.content

    def test_htmx_already_taken_seat_returns_partial(self, client, future_screening):
        seat = future_screening.seats.first()
        reserve_seat(seat.id)
        response = client.post(
            self._url(future_screening),
            {"seats": [seat.id]},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"already been reserved" in response.content
        assert seat.reservations.filter(status="confirmed").count() == 1


@pytest.mark.django_db
class TestBookingConfirmation:
    def test_confirmation_shows_every_seat_and_the_total(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:3])
        client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            {"seats": [seat.id for seat in seats]},
        )
        group_id = seats[0].reservations.get(status="confirmed").group_id

        response = client.get(reverse("booking-confirmation", args=[group_id]))
        assert response.status_code == 200
        for seat in seats:
            assert f"{seat.row}{seat.number}".encode() in response.content
        # 3 seats at the screening's base price of 14.50.
        assert b"43.50" in response.content

    def test_unknown_booking_404s(self, client):
        response = client.get(
            reverse(
                "booking-confirmation",
                args=["00000000-0000-0000-0000-000000000000"],
            )
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestCancelBooking:
    def _book(self, client, screening, count=2):
        seats = list(screening.seats.all()[:count])
        client.post(
            reverse("reserve-seats", args=[screening.id]),
            {"seats": [seat.id for seat in seats]},
        )
        return seats, seats[0].reservations.get(status="confirmed").group_id

    def test_cancel_frees_every_seat_in_the_booking(self, client, future_screening):
        seats, group_id = self._book(client, future_screening)
        response = client.post(reverse("cancel-booking", args=[group_id]))
        assert response.status_code == 302
        assert response.url == reverse("my-bookings")
        assert all(seat.is_available is True for seat in seats)

    def test_cancelled_seats_can_be_booked_again(self, client, future_screening):
        seats, group_id = self._book(client, future_screening)
        client.post(reverse("cancel-booking", args=[group_id]))

        client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            {"seats": [seat.id for seat in seats]},
        )
        assert all(seat.is_available is False for seat in seats)

    def test_get_does_not_cancel(self, client, future_screening):
        seats, group_id = self._book(client, future_screening)
        response = client.get(reverse("cancel-booking", args=[group_id]))
        assert response.status_code == 405
        assert all(seat.is_available is False for seat in seats)

    def test_cannot_cancel_a_booking_from_another_session(
        self, client, django_client_factory, future_screening
    ):
        seats, group_id = self._book(client, future_screening)

        stranger = django_client_factory()
        response = stranger.post(reverse("cancel-booking", args=[group_id]))

        assert response.status_code == 404
        assert all(seat.is_available is False for seat in seats)

    def test_cancelling_twice_is_reported_not_crashed(self, client, future_screening):
        _, group_id = self._book(client, future_screening)
        client.post(reverse("cancel-booking", args=[group_id]))
        response = client.post(reverse("cancel-booking", args=[group_id]), follow=True)
        assert response.status_code == 200
        assert b"not active" in response.content

    def test_htmx_cancel_returns_client_redirect(self, client, future_screening):
        seats, group_id = self._book(client, future_screening)
        response = client.post(
            reverse("cancel-booking", args=[group_id]), HTTP_HX_REQUEST="true"
        )
        assert response.status_code == 200
        assert response["HX-Redirect"] == reverse("my-bookings")
        assert all(seat.is_available is True for seat in seats)

    def test_confirmation_offers_cancelling_to_the_booker(
        self, client, future_screening
    ):
        _, group_id = self._book(client, future_screening)
        response = client.get(reverse("booking-confirmation", args=[group_id]))
        assert b"Cancel booking" in response.content

    def test_confirmation_hides_cancelling_from_others(
        self, client, django_client_factory, future_screening
    ):
        _, group_id = self._book(client, future_screening)
        stranger = django_client_factory()
        response = stranger.get(reverse("booking-confirmation", args=[group_id]))
        assert response.status_code == 200
        assert b"Cancel booking" not in response.content

    def test_partly_cancelled_booking_still_offers_cancelling(
        self, client, future_screening
    ):
        """Regression: a booking whose first seat was cancelled on its own (the
        admin can do this) used to report itself cancelled and hide the cancel
        control, stranding the seats that were still sold."""
        seats, group_id = self._book(client, future_screening, count=3)
        first = seats[0].reservations.get(status="confirmed")
        first.status = "cancelled"
        first.save(update_fields=["status"])

        response = client.get(reverse("booking-confirmation", args=[group_id]))
        assert b"Booking cancelled" not in response.content
        assert b"Cancel booking" in response.content

        # ...and cancelling then releases the seats that were still sold.
        client.post(reverse("cancel-booking", args=[group_id]))
        assert all(seat.is_available is True for seat in seats)

    def test_partly_cancelled_booking_still_lists_as_confirmed(
        self, client, future_screening
    ):
        seats, _ = self._book(client, future_screening, count=2)
        first = seats[0].reservations.get(status="confirmed")
        first.status = "cancelled"
        first.save(update_fields=["status"])

        response = client.get(reverse("my-bookings"))
        assert b"confirmed" in response.content

    def test_cancel_requires_a_csrf_token(self, client, future_screening):
        """The session check is not the only thing standing between a stranger
        and someone's seats: a cross-site POST carrying the victim's cookies
        has to be rejected by CSRF too."""
        seats, group_id = self._book(client, future_screening)

        # Same session (so the ownership check passes), but no CSRF token.
        forged = Client(enforce_csrf_checks=True)
        forged.cookies = client.cookies

        response = forged.post(reverse("cancel-booking", args=[group_id]))

        assert response.status_code == 403
        assert all(seat.is_available is False for seat in seats)

    def test_confirmation_shows_a_cancelled_booking_as_cancelled(
        self, client, future_screening
    ):
        _, group_id = self._book(client, future_screening)
        client.post(reverse("cancel-booking", args=[group_id]))
        response = client.get(reverse("booking-confirmation", args=[group_id]))
        assert response.status_code == 200
        assert b"Booking cancelled" in response.content
        assert b"Cancel booking" not in response.content


@pytest.mark.django_db
class TestMyBookings:
    def test_my_bookings_lists_bookings_from_this_session(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:2])
        client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            {"seats": [seat.id for seat in seats]},
        )
        response = client.get(reverse("my-bookings"))
        assert response.status_code == 200
        for seat in seats:
            assert f"{seat.row}{seat.number}".encode() in response.content

    def test_seats_booked_together_appear_as_one_booking(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:3])
        client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            {"seats": [seat.id for seat in seats]},
        )
        response = client.get(reverse("my-bookings"))
        assert response.content.count(b'class="booking"') == 1

    def test_my_bookings_empty_without_reservations(self, client):
        response = client.get(reverse("my-bookings"))
        assert response.status_code == 200
        assert b"no bookings" in response.content
