from django.contrib import admin

from .models import (
    Auditorium,
    BookingItem,
    MenuItem,
    Movie,
    Reservation,
    Screening,
    Seat,
)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "release_date", "runtime_minutes", "has_poster"]
    list_filter = ["release_date"]
    search_fields = ["title"]

    @admin.display(boolean=True, description="Poster")
    def has_poster(self, movie):
        return bool(movie.poster_image)


@admin.register(Auditorium)
class AuditoriumAdmin(admin.ModelAdmin):
    list_display = ["name", "screen_format", "surcharge", "seat_count"]
    list_filter = ["screen_format"]


@admin.register(Screening)
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ["movie", "auditorium", "start_time", "base_price"]
    list_filter = ["auditorium", "start_time"]
    search_fields = ["movie__title"]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["screening", "row", "number", "kind", "is_available"]
    list_filter = ["kind", "screening"]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["booking_id", "group_id", "seat", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["customer_name", "customer_email", "booking_id", "group_id"]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "is_available", "has_image"]
    list_filter = ["category", "is_available"]
    list_editable = ["price", "is_available"]
    search_fields = ["name"]

    @admin.display(boolean=True, description="Image")
    def has_image(self, item):
        return bool(item.image_url)


@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ["group_id", "item", "quantity", "unit_price", "line_total"]
    search_fields = ["group_id", "item__name"]
