"""A booking becomes a table instead of a shared UUID.

Seats and menu items were tied together by a `group_id` column that pointed at
nothing enforceable, and every reservation in a group repeated the customer's
name and email. Member discounts need somewhere to live that is not recomputed
at display time, which is what finally forced the issue.

Existing groups are converted into `Booking` rows, so no bookings are lost.
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def group_ids_become_bookings(apps, schema_editor):
    Booking = apps.get_model("cinema", "Booking")
    Reservation = apps.get_model("cinema", "Reservation")
    BookingItem = apps.get_model("cinema", "BookingItem")

    bookings = {}
    for reservation in Reservation.objects.all().order_by("created_at"):
        booking = bookings.get(reservation.group_id)
        if booking is None:
            booking = Booking.objects.create(
                reference=reservation.group_id,
                customer_name=reservation.customer_name,
                customer_email=reservation.customer_email,
            )
            bookings[reservation.group_id] = booking
        reservation.booking = booking
        reservation.save(update_fields=["booking"])

    for line in BookingItem.objects.all():
        booking = bookings.get(line.group_id)
        if booking is None:
            # Food with no seats should not exist, but do not lose the row.
            booking = Booking.objects.create(reference=line.group_id)
            bookings[line.group_id] = booking
        line.booking = booking
        line.save(update_fields=["booking"])


def bookings_become_group_ids(apps, schema_editor):
    for name in ("Reservation", "BookingItem"):
        model = apps.get_model("cinema", name)
        for row in model.objects.select_related("booking"):
            row.group_id = row.booking.reference
            row.save(update_fields=["group_id"])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cinema", "0005_menu_and_booking_items"),
    ]

    operations = [
        migrations.CreateModel(
            name="Booking",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("reference", models.UUIDField(default=uuid.uuid4, unique=True)),
                (
                    "customer_name",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "customer_email",
                    models.EmailField(blank=True, default="", max_length=254),
                ),
                ("discount", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="bookings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        # The old per-seat UUID must go first: the new FK's column is also
        # called booking_id, and SQLite refuses a duplicate column name.
        migrations.RemoveField(model_name="reservation", name="booking_id"),
        migrations.AddField(
            model_name="reservation",
            name="booking",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reservations",
                to="cinema.booking",
            ),
        ),
        migrations.AddField(
            model_name="bookingitem",
            name="booking",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="cinema.booking",
            ),
        ),
        migrations.RunPython(group_ids_become_bookings, bookings_become_group_ids),
        migrations.AlterField(
            model_name="reservation",
            name="booking",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reservations",
                to="cinema.booking",
            ),
        ),
        migrations.AlterField(
            model_name="bookingitem",
            name="booking",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="cinema.booking",
            ),
        ),
        migrations.RemoveField(model_name="reservation", name="group_id"),
        migrations.RemoveField(model_name="reservation", name="customer_name"),
        migrations.RemoveField(model_name="reservation", name="customer_email"),
        migrations.RemoveField(model_name="bookingitem", name="group_id"),
    ]
