"""The concession menu, and adding it to a booking."""

import urllib.error

import pytest
from django.core.management import call_command
from django.urls import reverse

from .commons import find_image
from .models import BookingItem, MenuItem
from .services import MAX_ITEM_QUANTITY, create_booking, parse_item_quantities

IMAGE_PAYLOAD = {
    "query": {
        "pages": {
            "1": {
                "imageinfo": [
                    {
                        "thumburl": "https://upload.wikimedia.org/thumb/popcorn.jpg",
                        "extmetadata": {
                            "Artist": {"value": '<a href="#">Ada</a>'},
                            "LicenseShortName": {"value": "CC0"},
                        },
                    }
                ]
            }
        }
    }
}


@pytest.fixture
def popcorn():
    return MenuItem.objects.create(
        name="Salted popcorn (L)",
        category=MenuItem.Category.POPCORN,
        price=700,
        image_source="File:Popcorn.jpg",
    )


@pytest.fixture
def cola():
    return MenuItem.objects.create(
        name="Cola (M)", category=MenuItem.Category.DRINKS, price=450
    )


class TestFindImage:
    def test_returns_url_and_credit(self):
        image = find_image("File:Popcorn.jpg", request=lambda title: IMAGE_PAYLOAD)
        assert image["url"] == "https://upload.wikimedia.org/thumb/popcorn.jpg"
        # The credit is assembled from stripped markup, so a licence that asks
        # for attribution gets it.
        assert image["credit"] == "Ada / CC0 / Wikimedia Commons"

    def test_missing_file_returns_none(self):
        payload = {"query": {"pages": {"-1": {"title": "File:Nope.jpg"}}}}
        assert find_image("File:Nope.jpg", request=lambda title: payload) is None

    @pytest.mark.parametrize(
        "error",
        [urllib.error.URLError("down"), TimeoutError(), OSError(), ValueError()],
    )
    def test_network_failures_return_none(self, error):
        def failing(title):
            raise error

        assert find_image("File:Popcorn.jpg", request=failing) is None


@pytest.mark.django_db
class TestFetchMenuImagesCommand:
    def test_sets_image_and_credit(self, monkeypatch, popcorn):
        monkeypatch.setattr(
            "cinema.management.commands.fetch_menu_images.find_image",
            lambda source: {"url": "https://example.com/p.jpg", "credit": "Ada / CC0"},
        )
        call_command("fetch_menu_images")
        popcorn.refresh_from_db()
        assert popcorn.image_url == "https://example.com/p.jpg"
        assert popcorn.image_credit == "Ada / CC0"

    def test_items_without_a_source_are_skipped(self, monkeypatch, cola):
        monkeypatch.setattr(
            "cinema.management.commands.fetch_menu_images.find_image",
            lambda source: {"url": "https://example.com/x.jpg", "credit": "x"},
        )
        call_command("fetch_menu_images")
        cola.refresh_from_db()
        assert cola.image_url == ""


@pytest.mark.django_db
class TestMenuPage:
    def test_menu_lists_items_with_prices(self, client, popcorn, cola):
        response = client.get(reverse("menu"))
        assert response.status_code == 200
        body = response.content.decode()
        assert popcorn.name in body
        assert "700" in body
        assert cola.name in body

    def test_unavailable_items_are_hidden(self, client, popcorn):
        popcorn.is_available = False
        popcorn.save(update_fields=["is_available"])
        response = client.get(reverse("menu"))
        assert popcorn.name not in response.content.decode()


@pytest.mark.django_db
class TestParseItemQuantities:
    def test_reads_requested_quantities(self, popcorn, cola):
        data = {f"item_{popcorn.id}": "2", f"item_{cola.id}": "1"}
        assert parse_item_quantities(data, [popcorn, cola]) == [(popcorn, 2), (cola, 1)]

    def test_ignores_blanks_zeroes_and_junk(self, popcorn, cola):
        for value in ["", "0", "-3", "two", None]:
            data = {f"item_{popcorn.id}": value}
            assert parse_item_quantities(data, [popcorn]) == []

    def test_caps_the_quantity(self, popcorn):
        data = {f"item_{popcorn.id}": "999"}
        assert parse_item_quantities(data, [popcorn]) == [(popcorn, MAX_ITEM_QUANTITY)]


@pytest.mark.django_db
class TestBookingWithFood:
    def test_items_are_attached_to_the_booking(self, future_screening, popcorn, cola):
        seat = future_screening.seats.first()
        booking = create_booking([seat.id], items=[(popcorn, 2), (cola, 1)])

        lines = BookingItem.objects.filter(booking=booking)
        assert lines.count() == 2
        assert sum(line.line_total for line in lines) == 700 * 2 + 450

    def test_price_is_snapshotted_so_a_menu_change_cannot_alter_a_booking(
        self, future_screening, popcorn
    ):
        seat = future_screening.seats.first()
        booking = create_booking([seat.id], items=[(popcorn, 2)])

        popcorn.price = 5000
        popcorn.save(update_fields=["price"])

        line = BookingItem.objects.get(booking=booking)
        assert line.unit_price == 700
        assert line.line_total == 1400

    def test_booking_without_food_has_no_lines(self, future_screening):
        seat = future_screening.seats.first()
        booking = create_booking([seat.id])
        assert not BookingItem.objects.filter(booking=booking).exists()


@pytest.mark.django_db
class TestFoodInTheBookingFlow:
    def _url(self, screening):
        return reverse("reserve-seats", args=[screening.id])

    def test_details_step_offers_the_menu(self, client, future_screening, popcorn):
        seat = future_screening.seats.first()
        response = client.post(self._url(future_screening), {"seats": [seat.id]})
        assert f'name="item_{popcorn.id}"'.encode() in response.content

    def test_chosen_quantities_survive_going_back_and_forth(
        self, client, future_screening, popcorn
    ):
        seat = future_screening.seats.first()
        response = client.post(
            self._url(future_screening),
            {"seats": [seat.id], f"item_{popcorn.id}": "3"},
        )
        assert b'value="3"' in response.content

    def test_confirming_records_the_food_and_the_grand_total(
        self, client, future_screening, popcorn
    ):
        seat = future_screening.seats.first()
        client.post(
            self._url(future_screening),
            {
                "seats": [seat.id],
                "step": "details",
                "customer_name": "Ada Lovelace",
                "customer_email": "ada@example.com",
                f"item_{popcorn.id}": "2",
            },
        )
        booking = seat.reservations.get(status="confirmed").booking
        assert BookingItem.objects.filter(booking=booking).count() == 1

        response = client.get(reverse("booking-confirmation", args=[booking.reference]))
        body = response.content.decode()
        assert "2 &times; Salted popcorn (L)" in body or "2 × Salted popcorn" in body
        # 2,000 seat + 1,400 popcorn.
        assert "3,400" in body

    def test_food_is_optional(self, client, future_screening, popcorn):
        seat = future_screening.seats.first()
        response = client.post(
            self._url(future_screening),
            {
                "seats": [seat.id],
                "step": "details",
                "customer_name": "Ada Lovelace",
                "customer_email": "ada@example.com",
            },
        )
        assert response.status_code == 302
        booking = seat.reservations.get(status="confirmed").booking
        assert not BookingItem.objects.filter(booking=booking).exists()
