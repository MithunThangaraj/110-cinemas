import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .layouts import LAYOUTS

# Number of colour schemes available for generated poster art.
POSTER_THEMES = 6


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    release_date = models.DateField()
    runtime_minutes = models.PositiveIntegerField()
    poster_image = models.URLField(blank=True)

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return self.title

    @property
    def poster_theme(self):
        """Colour scheme (1..POSTER_THEMES) for the generated poster art.

        Movies without a `poster_image` are shown as a coloured key-art card
        instead of a broken image. The colour is derived from the title so it
        stays the same across deploys, unlike one derived from the primary key
        (which changes whenever the demo data is reseeded).
        """
        return sum(ord(char) for char in self.title) % POSTER_THEMES + 1


class Auditorium(models.Model):
    """A physical screen. Its format decides both the seat map and the price."""

    class Format(models.TextChoices):
        STANDARD = "standard", "Standard"
        IMAX_GT = "imax_gt", "IMAX GT"
        DOLBY = "dolby", "Dolby Cinema"
        FOUR_DX = "4dx", "4DX"

    name = models.CharField(max_length=100, unique=True)
    screen_format = models.CharField(
        max_length=20, choices=Format.choices, default=Format.STANDARD
    )
    # Yen added to the screening's base price for every seat in this room.
    surcharge = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def layout(self):
        return LAYOUTS[self.screen_format]

    @property
    def seat_count(self):
        return self.layout.seat_count


class Screening(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="screenings"
    )
    auditorium = models.ForeignKey(
        Auditorium, on_delete=models.PROTECT, related_name="screenings"
    )
    start_time = models.DateTimeField()
    # Yen. The currency has no minor unit, so prices are whole numbers.
    base_price = models.PositiveIntegerField()

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return (
            f"{self.movie.title} @ {self.auditorium.name} "
            f"({self.start_time:%Y-%m-%d %H:%M})"
        )

    def price_for(self, seat_kind):
        """What one seat of this kind costs, in yen."""
        return self.base_price + self.auditorium.surcharge + Seat.SURCHARGES[seat_kind]

    @property
    def cheapest_price(self):
        return self.price_for(Seat.Kind.STANDARD)

    @property
    def premium_price(self):
        return self.price_for(Seat.Kind.PREMIUM)

    def clean(self):
        if self.start_time and self.start_time < timezone.now():
            raise ValidationError("Start time cannot be in the past.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


def generate_seats(screening):
    """Create the seats for a screening from its auditorium's layout."""
    layout = screening.auditorium.layout
    seats = [
        Seat(
            screening=screening,
            row=row,
            number=number,
            kind=layout.kind_for(row, number, count),
        )
        for row, count in layout.rows_with_seats()
        for number in range(1, count + 1)
    ]
    Seat.objects.bulk_create(seats)


class Seat(models.Model):
    class Kind(models.TextChoices):
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"
        WHEELCHAIR = "wheelchair", "Wheelchair space"

    # Yen added on top of the screening price and the auditorium surcharge.
    # Accessible spaces are never sold at the premium rate.
    SURCHARGES = {
        Kind.STANDARD: 0,
        Kind.PREMIUM: 500,
        Kind.WHEELCHAIR: 0,
    }

    screening = models.ForeignKey(
        Screening, on_delete=models.CASCADE, related_name="seats"
    )
    row = models.CharField(max_length=10)
    number = models.PositiveIntegerField()
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.STANDARD)

    class Meta:
        unique_together = ("screening", "row", "number")
        ordering = ["row", "number"]

    def __str__(self):
        return f"{self.row}{self.number} ({self.screening})"

    @property
    def label(self):
        return f"{self.row}{self.number}"

    @property
    def price(self):
        return self.screening.price_for(self.kind)

    @property
    def is_available(self):
        return not self.reservations.filter(
            status=Reservation.Status.CONFIRMED
        ).exists()


class MenuItem(models.Model):
    """Something sold at the concession stand."""

    class Category(models.TextChoices):
        POPCORN = "popcorn", "Popcorn"
        SNACKS = "snacks", "Snacks"
        DRINKS = "drinks", "Drinks"
        DESSERTS = "desserts", "Desserts"

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.SNACKS
    )
    # Yen, like ticket prices.
    price = models.PositiveIntegerField()
    image_url = models.URLField(blank=True)
    # Where the picture came from, so a licence that asks for credit gets it.
    image_credit = models.CharField(max_length=255, blank=True)
    # Wikimedia Commons file title, used to look the image up again.
    image_source = models.CharField(max_length=255, blank=True)
    is_available = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "sort_order", "name"]

    def __str__(self):
        return self.name


class BookingItem(models.Model):
    """A menu item added to a booking."""

    group_id = models.UUIDField(db_index=True)
    item = models.ForeignKey(
        MenuItem, on_delete=models.PROTECT, related_name="booking_items"
    )
    quantity = models.PositiveSmallIntegerField()
    # Snapshot of what it cost at the time. Menu prices change; a booking that
    # has already been paid for does not.
    unit_price = models.PositiveIntegerField()

    class Meta:
        ordering = ["item__category", "item__name"]

    def __str__(self):
        return f"{self.quantity} x {self.item.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Reservation(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    seat = models.ForeignKey(
        Seat, on_delete=models.CASCADE, related_name="reservations"
    )
    booking_id = models.UUIDField(default=uuid.uuid4, unique=True)
    # Seats reserved together in one booking share a group_id, so a visitor can
    # be shown (and can look up) their whole booking rather than one seat.
    group_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    customer_name = models.CharField(max_length=255, blank=True, default="")
    customer_email = models.EmailField(blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # The literal is deliberate: Status is not yet bound while this
            # Meta class body is being evaluated. This constraint is what
            # actually prevents a seat being double-booked.
            models.UniqueConstraint(
                fields=["seat", "status"],
                condition=Q(status="confirmed"),
                name="unique_active_reservation",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reservation {self.booking_id} - {self.seat} ({self.status})"
