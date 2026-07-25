import uuid
from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from .models import POSTER_THEMES, Movie, Reservation, Screening, Seat
from .services import (
    MAX_SEATS_PER_BOOKING,
    cancel_booking,
    cancel_reservation,
    create_booking,
    reserve_seat,
)


@pytest.mark.django_db
class TestMovie:
    def test_create_movie(self):
        movie = Movie.objects.create(
            title="Test Movie",
            release_date=date(2026, 1, 1),
            runtime_minutes=120,
        )
        assert movie.title == "Test Movie"
        assert str(movie) == "Test Movie"

    def test_poster_theme_is_in_range_and_stable(self):
        movie = Movie(title="Test Movie", release_date=date(2026, 1, 1))
        assert 1 <= movie.poster_theme <= POSTER_THEMES
        assert movie.poster_theme == Movie(title="Test Movie").poster_theme

    def test_poster_theme_differs_between_titles(self):
        # Not a guarantee for every pair, but the listing should not be a
        # single flat colour for these demo-style titles.
        titles = ["Dune", "Spirited Away", "Neon Harbour", "Paper Moons"]
        themes = {Movie(title=title).poster_theme for title in titles}
        assert len(themes) > 1

    def test_movie_ordering(self):
        Movie.objects.create(
            title="Older", release_date=date(2024, 1, 1), runtime_minutes=90
        )
        Movie.objects.create(
            title="Newer", release_date=date(2025, 1, 1), runtime_minutes=90
        )
        movies = Movie.objects.all()
        assert movies[0].title == "Newer"

    def test_movie_requires_title(self):
        with pytest.raises(ValidationError):
            movie = Movie(release_date=date(2026, 1, 1), runtime_minutes=120)
            movie.full_clean()


@pytest.mark.django_db
class TestScreening:
    def test_create_screening(self, movie):
        start = timezone.now() + timedelta(days=1)
        screening = Screening.objects.create(
            movie=movie,
            venue="Auditorium 1",
            start_time=start,
            base_price="14.50",
        )
        assert screening.movie == movie
        assert str(movie) in str(screening)

    def test_screening_past_start_time_raises(self, movie):
        past = timezone.now() - timedelta(days=1)
        with pytest.raises(ValidationError):
            Screening.objects.create(
                movie=movie,
                venue="Auditorium 1",
                start_time=past,
                base_price="14.50",
            )

    def test_screening_generates_seats(self, future_screening):
        seats = Seat.objects.filter(screening=future_screening)
        assert seats.count() == 96


@pytest.mark.django_db
class TestSeat:
    def test_seat_unique_together(self, future_screening):
        Seat.objects.create(screening=future_screening, row="Z", number=99)
        with pytest.raises(IntegrityError):
            Seat.objects.create(screening=future_screening, row="Z", number=99)

    def test_seat_available_by_default(self, future_screening):
        seat = future_screening.seats.first()
        assert seat.is_available is True

    def test_seat_not_available_when_reserved(self, future_screening):
        seat = future_screening.seats.first()
        Reservation.objects.create(seat=seat)
        assert seat.is_available is False


@pytest.mark.django_db
class TestReservation:
    def test_create_reservation(self, future_screening):
        seat = future_screening.seats.first()
        reservation = Reservation.objects.create(seat=seat)
        assert reservation.status == "confirmed"
        assert isinstance(reservation.booking_id, uuid.UUID)

    def test_unique_active_reservation(self, future_screening):
        seat = future_screening.seats.first()
        Reservation.objects.create(seat=seat)
        with pytest.raises(IntegrityError):
            Reservation.objects.create(seat=seat)

    def test_cancelled_reservation_allows_new(self, future_screening):
        seat = future_screening.seats.first()
        r1 = Reservation.objects.create(seat=seat)
        r1.status = "cancelled"
        r1.save(update_fields=["status"])
        r2 = Reservation.objects.create(seat=seat)
        assert r2.status == "confirmed"


@pytest.mark.django_db
class TestServices:
    def test_reserve_seat(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        assert reservation.status == "confirmed"
        assert reservation.seat == seat

    def test_reserve_already_reserved_seat(self, future_screening):
        seat = future_screening.seats.first()
        reserve_seat(seat.id)
        with pytest.raises(ValidationError):
            reserve_seat(seat.id)

    def test_cancel_reservation(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        cancel_reservation(reservation.id)
        reservation.refresh_from_db()
        assert reservation.status == "cancelled"

    def test_seat_available_after_cancel(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        cancel_reservation(reservation.id)
        assert seat.is_available is True

    def test_available_seats_query_excludes_reserved(self, future_screening):
        all_seats = list(future_screening.seats.all())
        first_seat = all_seats[0]
        second_seat = all_seats[1]
        reserve_seat(first_seat.id)
        available = [
            s for s in Seat.objects.filter(screening=future_screening) if s.is_available
        ]
        assert first_seat not in available
        assert second_seat in available


@pytest.mark.django_db
class TestCreateBooking:
    def test_seats_booked_together_share_a_group(self, future_screening):
        seats = list(future_screening.seats.all()[:3])
        reservations = create_booking([seat.id for seat in seats])
        assert len(reservations) == 3
        assert len({r.group_id for r in reservations}) == 1

    def test_separate_bookings_get_separate_groups(self, future_screening):
        seats = list(future_screening.seats.all()[:2])
        first = create_booking([seats[0].id])
        second = create_booking([seats[1].id])
        assert first[0].group_id != second[0].group_id

    def test_duplicate_seat_ids_are_booked_once(self, future_screening):
        seat = future_screening.seats.first()
        reservations = create_booking([seat.id, seat.id])
        assert len(reservations) == 1

    def test_empty_selection_is_rejected(self, future_screening):
        with pytest.raises(ValidationError):
            create_booking([])

    def test_more_than_the_limit_is_rejected(self, future_screening):
        seats = list(future_screening.seats.all()[: MAX_SEATS_PER_BOOKING + 1])
        with pytest.raises(ValidationError):
            create_booking([seat.id for seat in seats])

    def test_exactly_the_limit_is_allowed(self, future_screening):
        seats = list(future_screening.seats.all()[:MAX_SEATS_PER_BOOKING])
        reservations = create_booking([seat.id for seat in seats])
        assert len(reservations) == MAX_SEATS_PER_BOOKING

    def test_unknown_seat_id_is_rejected(self, future_screening):
        seat = future_screening.seats.first()
        with pytest.raises(ValidationError):
            create_booking([seat.id, 999999])

    def test_cancel_booking_cancels_every_seat(self, future_screening):
        seats = list(future_screening.seats.all()[:3])
        reservations = create_booking([seat.id for seat in seats])

        cancelled = cancel_booking(reservations[0].group_id)

        assert len(cancelled) == 3
        assert all(seat.is_available for seat in seats)

    def test_cancel_booking_leaves_other_bookings_alone(self, future_screening):
        seats = list(future_screening.seats.all()[:2])
        mine = create_booking([seats[0].id])
        theirs = create_booking([seats[1].id])

        cancel_booking(mine[0].group_id)

        theirs[0].refresh_from_db()
        assert theirs[0].status == "confirmed"
        assert seats[1].is_available is False

    def test_cancel_booking_twice_is_rejected(self, future_screening):
        seat = future_screening.seats.first()
        reservations = create_booking([seat.id])
        cancel_booking(reservations[0].group_id)
        with pytest.raises(ValidationError):
            cancel_booking(reservations[0].group_id)

    def test_cancel_unknown_booking_is_rejected(self):
        with pytest.raises(ValidationError):
            cancel_booking(uuid.uuid4())

    def test_one_taken_seat_books_none_of_them(self, future_screening):
        seats = list(future_screening.seats.all()[:3])
        reserve_seat(seats[2].id)
        with pytest.raises(ValidationError):
            create_booking([seat.id for seat in seats])
        assert seats[0].is_available is True
        assert seats[1].is_available is True
