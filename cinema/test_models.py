import uuid
from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from .layouts import LAYOUTS
from .models import (
    POSTER_THEMES,
    Auditorium,
    Booking,
    Movie,
    Reservation,
    Screening,
    Seat,
)
from .services import (
    MAX_SEATS_PER_BOOKING,
    cancel_booking,
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
    def test_create_screening(self, movie, auditorium):
        start = timezone.now() + timedelta(days=1)
        screening = Screening.objects.create(
            movie=movie,
            auditorium=auditorium,
            start_time=start,
            base_price=2000,
        )
        assert screening.movie == movie
        assert str(movie) in str(screening)
        assert auditorium.name in str(screening)

    def test_screening_past_start_time_raises(self, movie, auditorium):
        past = timezone.now() - timedelta(days=1)
        with pytest.raises(ValidationError):
            Screening.objects.create(
                movie=movie,
                auditorium=auditorium,
                start_time=past,
                base_price=2000,
            )

    def test_screening_generates_seats_for_its_layout(self, future_screening):
        seats = Seat.objects.filter(screening=future_screening)
        # A standard screen is 10 rows tapering from 15 seats to 18.
        assert seats.count() == 174
        assert future_screening.auditorium.seat_count == 174

    def test_imax_is_laid_out_larger_than_standard(
        self, movie, auditorium, imax_auditorium
    ):
        start = timezone.now() + timedelta(days=1)
        imax = Screening.objects.create(
            movie=movie, auditorium=imax_auditorium, start_time=start, base_price=2000
        )
        assert imax.seats.count() == 432
        assert imax.seats.count() > auditorium.seat_count

    def test_pricing_adds_format_and_seat_surcharges(self, movie, imax_auditorium):
        start = timezone.now() + timedelta(days=1)
        imax = Screening.objects.create(
            movie=movie, auditorium=imax_auditorium, start_time=start, base_price=2000
        )
        # 2000 base + 1000 IMAX surcharge, and premium seats add 500 more.
        assert imax.cheapest_price == 3000
        assert imax.premium_price == 3500

    def test_wheelchair_spaces_never_cost_the_premium_rate(self, future_screening):
        layout = future_screening.auditorium.layout
        space = future_screening.seats.get(row=layout.wheelchair_row, number=1)
        assert space.kind == Seat.Kind.WHEELCHAIR
        assert space.price == future_screening.cheapest_price

    def test_rows_taper_toward_the_screen(self, future_screening):
        """Rows nearest the screen hold fewer seats than the back rows."""
        counts = [
            future_screening.seats.filter(row=label).count()
            for label in future_screening.auditorium.layout.row_labels()
        ]
        assert counts[0] < counts[-1]
        # Never widening as you walk toward the screen.
        assert counts == sorted(counts)

    def test_every_layout_tapers(self):
        for screen_format, layout in LAYOUTS.items():
            counts = [layout.seats_in_row(i) for i in range(layout.rows)]
            assert counts[0] < counts[-1], screen_format
            assert counts == sorted(counts), screen_format

    def test_aisles_are_measured_from_both_ends_of_a_row(self):
        layout = LAYOUTS["standard"]
        # A short front row and a full back row both get two aisles, each the
        # same distance in from its end.
        for width in (layout.seats_in_row(0), layout.back_row_seats):
            aisles = [n for n in range(1, width + 1) if layout.is_aisle(n, width)]
            assert aisles == [layout.aisle_from_ends, width - layout.aisle_from_ends]

    def test_every_layout_has_wheelchair_spaces(self, movie, auditorium):
        for screen_format in Auditorium.Format.values:
            layout = LAYOUTS[screen_format]
            index = layout.row_labels().index(layout.wheelchair_row)
            width = layout.seats_in_row(index)
            ends = [1, 2, width - 1, width]
            kinds = {
                layout.kind_for(layout.wheelchair_row, number, width) for number in ends
            }
            assert kinds == {"wheelchair"}, screen_format


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
        reserve_seat(seat.id)
        assert seat.is_available is False


@pytest.mark.django_db
class TestReservation:
    def test_create_reservation(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        assert reservation.status == "confirmed"
        assert isinstance(reservation.booking.reference, uuid.UUID)

    def test_unique_active_reservation(self, future_screening):
        """The database itself refuses a second confirmed booking of a seat."""
        seat = future_screening.seats.first()
        booking = Booking.objects.create()
        Reservation.objects.create(seat=seat, booking=booking)
        with pytest.raises(IntegrityError):
            Reservation.objects.create(seat=seat, booking=booking)

    def test_cancelled_reservation_allows_new(self, future_screening):
        seat = future_screening.seats.first()
        booking = Booking.objects.create()
        first = Reservation.objects.create(seat=seat, booking=booking)
        first.status = "cancelled"
        first.save(update_fields=["status"])
        second = Reservation.objects.create(seat=seat, booking=booking)
        assert second.status == "confirmed"


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

    def test_cancel_booking_marks_the_reservation_cancelled(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        cancel_booking(reservation.booking)
        reservation.refresh_from_db()
        assert reservation.status == "cancelled"

    def test_seat_available_after_cancel(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        cancel_booking(reservation.booking)
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
        booking = create_booking([seat.id for seat in seats])
        assert booking.reservations.count() == 3

    def test_separate_bookings_get_separate_groups(self, future_screening):
        seats = list(future_screening.seats.all()[:2])
        first = create_booking([seats[0].id])
        second = create_booking([seats[1].id])
        assert first.reference != second.reference

    def test_duplicate_seat_ids_are_booked_once(self, future_screening):
        seat = future_screening.seats.first()
        booking = create_booking([seat.id, seat.id])
        assert booking.reservations.count() == 1

    def test_empty_selection_is_rejected(self, future_screening):
        with pytest.raises(ValidationError):
            create_booking([])

    def test_more_than_the_limit_is_rejected(self, future_screening):
        seats = list(future_screening.seats.all()[: MAX_SEATS_PER_BOOKING + 1])
        with pytest.raises(ValidationError):
            create_booking([seat.id for seat in seats])

    def test_exactly_the_limit_is_allowed(self, future_screening):
        seats = list(future_screening.seats.all()[:MAX_SEATS_PER_BOOKING])
        booking = create_booking([seat.id for seat in seats])
        assert booking.reservations.count() == MAX_SEATS_PER_BOOKING

    def test_unknown_seat_id_is_rejected(self, future_screening):
        seat = future_screening.seats.first()
        with pytest.raises(ValidationError):
            create_booking([seat.id, 999999])

    def test_cancel_booking_cancels_every_seat(self, future_screening):
        seats = list(future_screening.seats.all()[:3])
        booking = create_booking([seat.id for seat in seats])

        cancelled = cancel_booking(booking)

        assert len(cancelled) == 3
        assert all(seat.is_available for seat in seats)

    def test_cancel_booking_leaves_other_bookings_alone(self, future_screening):
        seats = list(future_screening.seats.all()[:2])
        mine = create_booking([seats[0].id])
        theirs = create_booking([seats[1].id])

        cancel_booking(mine)

        theirs_reservation = theirs.reservations.first()
        theirs_reservation.refresh_from_db()
        assert theirs_reservation.status == "confirmed"
        assert seats[1].is_available is False

    def test_cancel_booking_twice_is_rejected(self, future_screening):
        seat = future_screening.seats.first()
        booking = create_booking([seat.id])
        cancel_booking(booking)
        with pytest.raises(ValidationError):
            cancel_booking(booking)

    def test_cancel_unknown_booking_is_rejected(self):
        with pytest.raises(ValidationError):
            cancel_booking(Booking.objects.create())

    def test_one_taken_seat_books_none_of_them(self, future_screening):
        seats = list(future_screening.seats.all()[:3])
        reserve_seat(seats[2].id)
        with pytest.raises(ValidationError):
            create_booking([seat.id for seat in seats])
        assert seats[0].is_available is True
        assert seats[1].is_available is True
