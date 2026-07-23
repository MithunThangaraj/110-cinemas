import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


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


class Screening(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="screenings"
    )
    venue = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    base_price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.movie.title} @ {self.venue} ({self.start_time:%Y-%m-%d %H:%M})"

    def clean(self):
        if self.start_time and self.start_time < timezone.now():
            raise ValidationError("Start time cannot be in the past.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


SEAT_ROWS = 8
SEAT_COLS = 12


def generate_seats(screening, rows=SEAT_ROWS, cols=SEAT_COLS):
    seats = []
    for r in range(rows):
        row_label = chr(65 + r)
        for c in range(1, cols + 1):
            seats.append(Seat(screening=screening, row=row_label, number=c))
    Seat.objects.bulk_create(seats)


class Seat(models.Model):
    screening = models.ForeignKey(
        Screening, on_delete=models.CASCADE, related_name="seats"
    )
    row = models.CharField(max_length=10)
    number = models.PositiveIntegerField()

    class Meta:
        unique_together = ("screening", "row", "number")
        ordering = ["row", "number"]

    def __str__(self):
        return f"{self.row}{self.number} ({self.screening})"

    @property
    def is_available(self):
        return not self.reservations.filter(status="confirmed").exists()


class Reservation(models.Model):
    seat = models.ForeignKey(
        Seat, on_delete=models.CASCADE, related_name="reservations"
    )
    booking_id = models.UUIDField(default=uuid.uuid4, unique=True)
    customer_name = models.CharField(max_length=255, blank=True, default="")
    customer_email = models.EmailField(blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=[("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        default="confirmed",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["seat", "status"],
                condition=Q(status="confirmed"),
                name="unique_active_reservation",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reservation {self.booking_id} - {self.seat} ({self.status})"
