from django.contrib import admin

from .models import Movie, Reservation, Screening, Seat


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "release_date", "runtime_minutes"]
    list_filter = ["release_date"]
    search_fields = ["title"]


@admin.register(Screening)
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ["movie", "venue", "start_time", "base_price"]
    list_filter = ["venue", "start_time"]
    search_fields = ["movie__title"]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["screening", "row", "number", "is_available"]
    list_filter = ["screening"]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["booking_id", "seat", "customer_name", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["customer_name", "customer_email", "booking_id"]
