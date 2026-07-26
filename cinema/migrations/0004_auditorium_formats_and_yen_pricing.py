"""Screens become real auditoriums with their own layouts, and prices go to yen.

`Screening.venue` was free text and every screening got the same 8x12 grid, so
an IMAX screening had the same seat map as the smallest standard screen. A
screening now belongs to an `Auditorium`, whose format decides both the seat
map and the surcharge.

Note on existing data: seats are regenerated from the new layouts, which drops
the reservations attached to them. A booking for seat "H12" cannot be carried
into a room with a different shape, and the only rows here are seeded demo
data (the deployed database is rebuilt on every deploy anyway).
"""

import django.db.models.deletion
from django.db import migrations, models

from cinema.layouts import LAYOUTS

# (name, format, surcharge in yen). Surcharges follow Japanese multiplex
# pricing: premium formats cost more, 4DX most of all.
DEFAULT_AUDITORIUMS = [
    ("IMAX GT", "imax_gt", 1000),
    ("Dolby Cinema", "dolby", 1000),
    ("4DX Screen 3", "4dx", 1200),
    ("Screen 5", "standard", 0),
    ("Screen 6", "standard", 0),
]

BASE_PRICE_YEN = 2000


def build_auditoriums_and_relay_out_screens(apps, schema_editor):
    Auditorium = apps.get_model("cinema", "Auditorium")
    Screening = apps.get_model("cinema", "Screening")
    Seat = apps.get_model("cinema", "Seat")

    # Nothing to relocate on a fresh database (a test database, or a new
    # deploy). Creating rooms here anyway would plant fixture data in every
    # environment; `seed_demo_data` is what populates an empty install.
    if not Screening.objects.exists():
        return

    for name, screen_format, surcharge in DEFAULT_AUDITORIUMS:
        Auditorium.objects.get_or_create(
            name=name,
            defaults={"screen_format": screen_format, "surcharge": surcharge},
        )

    fallback = Auditorium.objects.get(name="Screen 5")
    by_name = {a.name: a for a in Auditorium.objects.all()}

    for screening in Screening.objects.all():
        # Old venues were free text such as "Screen 1 - IMAX"; match loosely
        # and fall back to a standard screen.
        venue = (screening.venue or "").lower()
        if "imax" in venue:
            auditorium = by_name["IMAX GT"]
        elif "dolby" in venue:
            auditorium = by_name["Dolby Cinema"]
        elif "4dx" in venue:
            auditorium = by_name["4DX Screen 3"]
        else:
            auditorium = fallback

        screening.auditorium = auditorium
        screening.base_price = BASE_PRICE_YEN
        screening.save(update_fields=["auditorium", "base_price"])

        # Lay the room out again to match its new format.
        Seat.objects.filter(screening=screening).delete()
        layout = LAYOUTS[auditorium.screen_format]
        Seat.objects.bulk_create(
            [
                Seat(
                    screening=screening,
                    row=row,
                    number=number,
                    kind=layout.kind_for(row, number),
                )
                for row in layout.row_labels()
                for number in range(1, layout.seats_per_row + 1)
            ]
        )


def unassign(apps, schema_editor):
    apps.get_model("cinema", "Screening").objects.update(auditorium=None)


class Migration(migrations.Migration):

    dependencies = [("cinema", "0003_reservation_group_id")]

    operations = [
        migrations.CreateModel(
            name="Auditorium",
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
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "screen_format",
                    models.CharField(
                        choices=[
                            ("standard", "Standard"),
                            ("imax_gt", "IMAX GT"),
                            ("dolby", "Dolby Cinema"),
                            ("4dx", "4DX"),
                        ],
                        default="standard",
                        max_length=20,
                    ),
                ),
                ("surcharge", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="seat",
            name="kind",
            field=models.CharField(
                choices=[
                    ("standard", "Standard"),
                    ("premium", "Premium"),
                    ("wheelchair", "Wheelchair space"),
                ],
                default="standard",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="screening",
            name="auditorium",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="screenings",
                to="cinema.auditorium",
            ),
        ),
        migrations.RunPython(build_auditoriums_and_relay_out_screens, unassign),
        migrations.AlterField(
            model_name="screening",
            name="auditorium",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="screenings",
                to="cinema.auditorium",
            ),
        ),
        migrations.RemoveField(model_name="screening", name="venue"),
        migrations.AlterField(
            model_name="screening",
            name="base_price",
            field=models.PositiveIntegerField(),
        ),
    ]
