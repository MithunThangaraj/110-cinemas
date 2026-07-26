"""Accounts, the member discount, and guest booking staying possible."""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Booking
from .services import create_booking

PASSWORD = "a-long-enough-passphrase"


@pytest.fixture
def member(db):
    return User.objects.create_user(
        username="ada", email="ada@example.com", password=PASSWORD
    )


def book(client, screening, seats, **overrides):
    payload = {
        "seats": [seat.id for seat in seats],
        "step": "details",
        "customer_name": "Ada Lovelace",
        "customer_email": "ada@example.com",
    }
    payload.update(overrides)
    return client.post(reverse("reserve-seats", args=[screening.id]), payload)


@pytest.mark.django_db
class TestSignUp:
    def test_creates_an_account_and_signs_in(self, client):
        response = client.post(
            reverse("sign-up"),
            {
                "username": "ada",
                "email": "ada@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(username="ada").exists()
        assert client.session.get("_auth_user_id")

    def test_duplicate_email_is_rejected(self, client, member):
        response = client.post(
            reverse("sign-up"),
            {
                "username": "someone-else",
                "email": "ADA@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
            },
        )
        assert response.status_code == 200
        assert b"already exists" in response.content
        assert User.objects.count() == 1

    def test_page_states_the_discount(self, client):
        response = client.get(reverse("sign-up"))
        assert str(Booking.MEMBER_DISCOUNT).encode() in response.content


@pytest.mark.django_db
class TestLogInOut:
    def test_member_can_log_in(self, client, member):
        response = client.post(
            reverse("log-in"), {"username": "ada", "password": PASSWORD}
        )
        assert response.status_code == 302
        assert client.session.get("_auth_user_id")

    def test_log_out(self, client, member):
        client.force_login(member)
        response = client.post(reverse("log-out"))
        assert response.status_code == 302
        assert not client.session.get("_auth_user_id")


@pytest.mark.django_db
class TestMemberDiscount:
    def test_a_member_booking_records_the_discount(
        self, client, member, future_screening
    ):
        client.force_login(member)
        seats = list(future_screening.seats.all()[:2])

        book(client, future_screening, seats)

        booking = seats[0].reservations.get(status="confirmed").booking
        assert booking.user == member
        assert booking.discount == Booking.MEMBER_DISCOUNT
        # 2 standard seats at 2,000 each, less the member discount.
        assert booking.total == 4000 - Booking.MEMBER_DISCOUNT

    def test_a_guest_booking_gets_no_discount(self, client, future_screening):
        seats = list(future_screening.seats.all()[:2])
        book(client, future_screening, seats)

        booking = seats[0].reservations.get(status="confirmed").booking
        assert booking.user is None
        assert booking.discount == 0
        assert booking.total == 4000

    def test_the_discount_applies_once_per_booking_not_per_seat(
        self, client, member, future_screening
    ):
        client.force_login(member)
        seats = list(future_screening.seats.all()[:6])

        book(client, future_screening, seats)

        booking = seats[0].reservations.get(status="confirmed").booking
        assert booking.discount == Booking.MEMBER_DISCOUNT
        assert booking.total == 6 * 2000 - Booking.MEMBER_DISCOUNT

    def test_the_total_never_goes_below_zero(self, member, future_screening):
        seat = future_screening.seats.first()
        booking = create_booking([seat.id], user=member)
        booking.discount = 999999
        booking.save(update_fields=["discount"])
        assert booking.total == 0

    def test_changing_the_offer_cannot_rewrite_a_past_booking(
        self, client, member, future_screening, monkeypatch
    ):
        client.force_login(member)
        seats = list(future_screening.seats.all()[:1])
        book(client, future_screening, seats)
        booking = seats[0].reservations.get(status="confirmed").booking

        # The offer changes tomorrow; this booking must not move.
        monkeypatch.setattr(Booking, "MEMBER_DISCOUNT", 5000)
        booking.refresh_from_db()
        assert booking.discount == 500

    def test_the_details_step_offers_the_discount_to_guests(
        self, client, future_screening
    ):
        seat = future_screening.seats.first()
        response = client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            {"seats": [seat.id]},
        )
        assert b"Create a free account" in response.content

    def test_the_details_step_shows_a_member_their_discount(
        self, client, member, future_screening
    ):
        client.force_login(member)
        seat = future_screening.seats.first()
        response = client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            {"seats": [seat.id]},
        )
        assert b"Member discount" in response.content
        assert b"Create a free account" not in response.content

    def test_a_member_does_not_retype_their_details(
        self, client, member, future_screening
    ):
        client.force_login(member)
        seat = future_screening.seats.first()
        response = client.post(
            reverse("reserve-seats", args=[future_screening.id]),
            {"seats": [seat.id]},
        )
        assert b"ada@example.com" in response.content


@pytest.mark.django_db
class TestGuestBookingStillWorks:
    def test_a_guest_can_book_without_an_account(self, client, future_screening):
        seat = future_screening.seats.first()
        response = book(client, future_screening, [seat])
        assert response.status_code == 302
        assert seat.is_available is False

    def test_a_guest_sees_their_booking_in_this_session(self, client, future_screening):
        seat = future_screening.seats.first()
        book(client, future_screening, [seat])
        response = client.get(reverse("my-bookings"))
        assert seat.label.encode() in response.content

    def test_another_guest_does_not_see_it(
        self, client, django_client_factory, future_screening
    ):
        seat = future_screening.seats.first()
        book(client, future_screening, [seat])

        stranger = django_client_factory()
        response = stranger.get(reverse("my-bookings"))
        assert b"no bookings" in response.content


@pytest.mark.django_db
class TestMemberBookingHistory:
    def test_a_member_sees_their_bookings_in_a_new_session(
        self, client, django_client_factory, member, future_screening
    ):
        """The point of an account: bookings outlive the browser session."""
        client.force_login(member)
        seat = future_screening.seats.first()
        book(client, future_screening, [seat])

        fresh = django_client_factory()
        fresh.force_login(member)
        response = fresh.get(reverse("my-bookings"))

        assert seat.label.encode() in response.content

    def test_a_member_cannot_see_another_member_s_bookings(
        self, client, django_client_factory, member, future_screening
    ):
        client.force_login(member)
        seat = future_screening.seats.first()
        book(client, future_screening, [seat])

        other = User.objects.create_user(username="bob", password=PASSWORD)
        stranger = django_client_factory()
        stranger.force_login(other)
        response = stranger.get(reverse("my-bookings"))

        assert b"no bookings" in response.content

    def test_a_member_can_cancel_from_a_new_session(
        self, client, django_client_factory, member, future_screening
    ):
        client.force_login(member)
        seat = future_screening.seats.first()
        book(client, future_screening, [seat])
        reference = seat.reservations.get(status="confirmed").booking.reference

        fresh = django_client_factory()
        fresh.force_login(member)
        response = fresh.post(reverse("cancel-booking", args=[reference]))

        assert response.status_code == 302
        assert seat.is_available is True

    def test_a_stranger_still_cannot_cancel(
        self, client, django_client_factory, member, future_screening
    ):
        client.force_login(member)
        seat = future_screening.seats.first()
        book(client, future_screening, [seat])
        reference = seat.reservations.get(status="confirmed").booking.reference

        other = User.objects.create_user(username="bob", password=PASSWORD)
        stranger = django_client_factory()
        stranger.force_login(other)
        response = stranger.post(reverse("cancel-booking", args=[reference]))

        assert response.status_code == 404
        assert seat.is_available is False
