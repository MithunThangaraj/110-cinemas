import re
from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from .models import Auditorium, Screening, Seat
from .services import (
    MAX_SEATS_PER_BOOKING,
    availability_signature,
    create_booking,
    reserve_seat,
)

DETAILS = {
    "step": "details",
    "customer_name": "Ada Lovelace",
    "customer_email": "ada@example.com",
}


def booking_payload(seats, **overrides):
    """Everything the final step of the booking flow submits."""
    payload = {"seats": [seat.id for seat in seats], **DETAILS}
    payload.update(overrides)
    return payload


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
class TestSeatAvailabilityPolling:
    def _url(self, screening):
        return reverse("seat-availability", args=[screening.id])

    def _chosen_seats(self, response):
        """The seat labels the re-rendered checkout says are selected."""
        match = re.search(
            r'<strong class="checkout__seats">(.*?)</strong>',
            response.content.decode(),
            re.S,
        )
        listed = match.group(1).strip()
        if listed == "none chosen yet":
            return []
        return [label.strip() for label in listed.split(",")]

    def test_no_change_returns_204_so_htmx_leaves_the_dom_alone(
        self, client, future_screening
    ):
        signature = availability_signature(future_screening)
        response = client.get(self._url(future_screening), {"v": signature})
        assert response.status_code == 204
        assert response.content == b""

    def test_a_new_booking_makes_the_map_refresh(self, client, future_screening):
        stale = availability_signature(future_screening)
        create_booking([future_screening.seats.first().id])

        response = client.get(self._url(future_screening), {"v": stale})

        assert response.status_code == 200
        assert b"<html" not in response.content

    def test_refresh_keeps_the_seats_the_visitor_had_chosen(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:3])
        stale = availability_signature(future_screening)
        # Somebody else books a seat this visitor had not chosen.
        create_booking([future_screening.seats.all()[10].id])

        response = client.get(
            self._url(future_screening),
            {"v": stale, "seats": [seat.id for seat in seats]},
        )

        chosen = self._chosen_seats(response)
        assert chosen == [seat.label for seat in seats]

    def test_refresh_drops_and_reports_a_seat_someone_else_took(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:3])
        stale = availability_signature(future_screening)
        create_booking([seats[0].id])

        response = client.get(
            self._url(future_screening),
            {"v": stale, "seats": [seat.id for seat in seats]},
        )

        body = response.content.decode()
        assert f"Someone just booked {seats[0].label}" in body
        # The seat that went is dropped; the other two stay chosen.
        assert self._chosen_seats(response) == [seats[1].label, seats[2].label]

    def test_signature_changes_when_a_seat_is_booked(self, future_screening):
        before = availability_signature(future_screening)
        create_booking([future_screening.seats.first().id])
        assert availability_signature(future_screening) != before

    def test_missing_screening_404s(self, client):
        response = client.get(reverse("seat-availability", args=[9999]))
        assert response.status_code == 404


@pytest.mark.django_db
class TestSeatMapQueryCount:
    def test_seat_map_does_not_scale_queries_with_seat_count(
        self, client, django_assert_max_num_queries, movie, imax_auditorium
    ):
        """Seat.is_available would be one query per seat - 432 of them here."""
        screening = Screening.objects.create(
            movie=movie,
            auditorium=imax_auditorium,
            start_time=timezone.now() + timedelta(days=2),
            base_price=2000,
        )
        assert screening.seats.count() == 432

        with django_assert_max_num_queries(12):
            response = client.get(reverse("seat-selection", args=[screening.id]))
        assert response.status_code == 200


@pytest.mark.django_db
class TestBookingDetailsStep:
    """Choosing seats leads to a details step; only that step books."""

    def _url(self, screening):
        return reverse("reserve-seats", args=[screening.id])

    def test_choosing_seats_asks_for_details_and_books_nothing(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:2])
        response = client.post(
            self._url(future_screening), {"seats": [seat.id for seat in seats]}
        )
        assert response.status_code == 200
        assert b"customer_name" in response.content
        assert b"customer_email" in response.content
        # Nothing is booked until the details step is submitted.
        assert all(seat.is_available is True for seat in seats)

    def test_details_step_shows_the_chosen_seats_and_total(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:3])
        response = client.post(
            self._url(future_screening), {"seats": [seat.id for seat in seats]}
        )
        body = response.content.decode()
        for seat in seats:
            assert seat.label in body
        assert "6,000" in body

    def test_submitting_details_books_and_records_who_for(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:2])
        response = client.post(self._url(future_screening), booking_payload(seats))
        assert response.status_code == 302
        booking = seats[0].reservations.get(status="confirmed").booking
        assert booking.customer_name == "Ada Lovelace"
        assert booking.customer_email == "ada@example.com"

    def test_invalid_details_re_render_the_step_without_booking(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:2])
        response = client.post(
            self._url(future_screening),
            booking_payload(seats, customer_email="not-an-email"),
        )
        assert response.status_code == 200
        assert b"customer_email" in response.content
        assert all(seat.is_available is True for seat in seats)

    def test_missing_name_re_renders_the_step_without_booking(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:2])
        response = client.post(
            self._url(future_screening), booking_payload(seats, customer_name="")
        )
        assert response.status_code == 200
        assert all(seat.is_available is True for seat in seats)

    def test_going_back_returns_to_the_map_with_the_selection_intact(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:3])
        response = client.post(
            self._url(future_screening),
            {"seats": [seat.id for seat in seats], "step": "seats"},
        )
        assert response.status_code == 200
        assert b'type="checkbox"' in response.content
        body = response.content.decode()
        for seat in seats:
            assert f'value="{seat.id}"' in body
        assert all(seat.is_available is True for seat in seats)

    def test_a_seat_taken_while_typing_sends_them_back_to_the_map(
        self, client, future_screening
    ):
        seats = list(future_screening.seats.all()[:2])
        # Seats are not held during the details step.
        create_booking([seats[0].id])

        response = client.post(self._url(future_screening), booking_payload(seats))

        assert response.status_code == 200
        assert b"already been reserved" in response.content
        assert b'type="checkbox"' in response.content
        assert seats[1].is_available is True

    def test_htmx_details_step_is_a_partial(self, client, future_screening):
        seats = list(future_screening.seats.all()[:2])
        response = client.post(
            self._url(future_screening),
            {"seats": [seat.id for seat in seats]},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"<html" not in response.content
        assert b"customer_name" in response.content


@pytest.mark.django_db
class TestReserveSeats:
    def _url(self, screening):
        return reverse("reserve-seats", args=[screening.id])

    def test_reserve_one_seat_redirects_to_confirmation(self, client, future_screening):
        seat = future_screening.seats.first()
        response = client.post(self._url(future_screening), booking_payload([seat]))
        seat.refresh_from_db()
        assert response.status_code == 302
        assert seat.is_available is False
        booking = seat.reservations.get(status="confirmed").booking
        assert response.url == reverse("booking-confirmation", args=[booking.reference])

    def test_reserve_several_seats_creates_one_booking(self, client, future_screening):
        seats = list(future_screening.seats.all()[:4])
        response = client.post(self._url(future_screening), booking_payload(seats))
        assert response.status_code == 302
        bookings = {
            seat.reservations.get(status="confirmed").booking_id for seat in seats
        }
        assert len(bookings) == 1

    def test_reserve_at_the_limit_is_allowed(self, client, future_screening):
        seats = list(future_screening.seats.all()[:MAX_SEATS_PER_BOOKING])
        client.post(self._url(future_screening), booking_payload(seats))
        assert all(seat.is_available is False for seat in seats)

    def test_reserve_over_the_limit_books_nothing(self, client, future_screening):
        seats = list(future_screening.seats.all()[: MAX_SEATS_PER_BOOKING + 1])
        response = client.post(self._url(future_screening), booking_payload(seats))
        assert response.status_code == 200
        assert b"at most" in response.content
        assert all(seat.is_available is True for seat in seats)

    def test_reserve_remembers_booking_in_session(self, client, future_screening):
        seat = future_screening.seats.first()
        client.post(self._url(future_screening), booking_payload([seat]))
        booking = seat.reservations.get(status="confirmed").booking
        assert str(booking.reference) in client.session["booking_references"]

    def test_reserve_without_seat_shows_error(self, client, future_screening):
        response = client.post(self._url(future_screening), {})
        assert response.status_code == 200
        assert b"choose a seat" in response.content
        assert future_screening.seats.first().is_available is True

    def test_seat_from_another_screening_is_ignored(
        self, client, future_screening, movie
    ):
        other = Screening.objects.create(
            movie=movie,
            auditorium=Auditorium.objects.create(name="Screen 9"),
            start_time=timezone.now() + timedelta(days=5),
            base_price=2000,
        )
        foreign_seat = other.seats.first()
        response = client.post(
            self._url(future_screening), booking_payload([foreign_seat])
        )
        assert response.status_code == 200
        assert b"choose a seat" in response.content
        assert foreign_seat.is_available is True

    def test_reserve_already_taken_seat_books_nothing(self, client, future_screening):
        seats = list(future_screening.seats.all()[:3])
        reserve_seat(seats[-1].id)
        response = client.post(self._url(future_screening), booking_payload(seats))
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
            booking_payload(seats),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        booking = seats[0].reservations.get(status="confirmed").booking
        assert response["HX-Redirect"] == reverse(
            "booking-confirmation", args=[booking.reference]
        )
        assert str(booking.reference) in client.session["booking_references"]

    def test_htmx_without_seat_returns_partial_error(self, client, future_screening):
        response = client.post(self._url(future_screening), {}, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert b"<html" not in response.content
        assert b"choose a seat" in response.content

    def test_htmx_over_the_limit_returns_partial(self, client, future_screening):
        seats = list(future_screening.seats.all()[: MAX_SEATS_PER_BOOKING + 1])
        response = client.post(
            self._url(future_screening),
            booking_payload(seats),
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
            booking_payload([seat]),
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
            booking_payload(seats),
        )
        reference = seats[0].reservations.get(status="confirmed").booking.reference

        response = client.get(reverse("booking-confirmation", args=[reference]))
        assert response.status_code == 200
        for seat in seats:
            assert f"{seat.row}{seat.number}".encode() in response.content
        # Three standard seats at the base price of 2,000 yen.
        assert b"6,000" in response.content

    def test_confirmation_shows_who_booked_it(self, client, future_screening):
        seats = list(future_screening.seats.all()[:2])
        client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            booking_payload(seats),
        )
        reference = seats[0].reservations.get(status="confirmed").booking.reference

        response = client.get(reverse("booking-confirmation", args=[reference]))

        assert b"Ada Lovelace" in response.content
        assert b"ada@example.com" in response.content

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
            booking_payload(seats),
        )
        return seats, seats[0].reservations.get(status="confirmed").booking.reference

    def test_cancel_frees_every_seat_in_the_booking(self, client, future_screening):
        seats, reference = self._book(client, future_screening)
        response = client.post(reverse("cancel-booking", args=[reference]))
        assert response.status_code == 302
        assert response.url == reverse("my-bookings")
        assert all(seat.is_available is True for seat in seats)

    def test_cancelled_seats_can_be_booked_again(self, client, future_screening):
        seats, reference = self._book(client, future_screening)
        client.post(reverse("cancel-booking", args=[reference]))

        client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            booking_payload(seats),
        )
        assert all(seat.is_available is False for seat in seats)

    def test_get_does_not_cancel(self, client, future_screening):
        seats, reference = self._book(client, future_screening)
        response = client.get(reverse("cancel-booking", args=[reference]))
        assert response.status_code == 405
        assert all(seat.is_available is False for seat in seats)

    def test_cannot_cancel_a_booking_from_another_session(
        self, client, django_client_factory, future_screening
    ):
        seats, reference = self._book(client, future_screening)

        stranger = django_client_factory()
        response = stranger.post(reverse("cancel-booking", args=[reference]))

        assert response.status_code == 404
        assert all(seat.is_available is False for seat in seats)

    def test_cancelling_twice_is_reported_not_crashed(self, client, future_screening):
        _, reference = self._book(client, future_screening)
        client.post(reverse("cancel-booking", args=[reference]))
        response = client.post(reverse("cancel-booking", args=[reference]), follow=True)
        assert response.status_code == 200
        assert b"not active" in response.content

    def test_htmx_cancel_returns_client_redirect(self, client, future_screening):
        seats, reference = self._book(client, future_screening)
        response = client.post(
            reverse("cancel-booking", args=[reference]), HTTP_HX_REQUEST="true"
        )
        assert response.status_code == 200
        assert response["HX-Redirect"] == reverse("my-bookings")
        assert all(seat.is_available is True for seat in seats)

    def test_confirmation_offers_cancelling_to_the_booker(
        self, client, future_screening
    ):
        _, reference = self._book(client, future_screening)
        response = client.get(reverse("booking-confirmation", args=[reference]))
        assert b"Cancel booking" in response.content

    def test_confirmation_hides_cancelling_from_others(
        self, client, django_client_factory, future_screening
    ):
        _, reference = self._book(client, future_screening)
        stranger = django_client_factory()
        response = stranger.get(reverse("booking-confirmation", args=[reference]))
        assert response.status_code == 200
        assert b"Cancel booking" not in response.content

    def test_partly_cancelled_booking_still_offers_cancelling(
        self, client, future_screening
    ):
        """Regression: a booking whose first seat was cancelled on its own (the
        admin can do this) used to report itself cancelled and hide the cancel
        control, stranding the seats that were still sold."""
        seats, reference = self._book(client, future_screening, count=3)
        first = seats[0].reservations.get(status="confirmed")
        first.status = "cancelled"
        first.save(update_fields=["status"])

        response = client.get(reverse("booking-confirmation", args=[reference]))
        assert b"Booking cancelled" not in response.content
        assert b"Cancel booking" in response.content

        # ...and cancelling then releases the seats that were still sold.
        client.post(reverse("cancel-booking", args=[reference]))
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
        seats, reference = self._book(client, future_screening)

        # Same session (so the ownership check passes), but no CSRF token.
        forged = Client(enforce_csrf_checks=True)
        forged.cookies = client.cookies

        response = forged.post(reverse("cancel-booking", args=[reference]))

        assert response.status_code == 403
        assert all(seat.is_available is False for seat in seats)

    def test_confirmation_shows_a_cancelled_booking_as_cancelled(
        self, client, future_screening
    ):
        _, reference = self._book(client, future_screening)
        client.post(reverse("cancel-booking", args=[reference]))
        response = client.get(reverse("booking-confirmation", args=[reference]))
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
            booking_payload(seats),
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
            booking_payload(seats),
        )
        response = client.get(reverse("my-bookings"))
        assert response.content.count(b'class="booking"') == 1

    def test_my_bookings_empty_without_reservations(self, client):
        response = client.get(reverse("my-bookings"))
        assert response.status_code == 200
        assert b"no bookings" in response.content
