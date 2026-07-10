"""
URL configuration for cinema project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from cinema import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("movies/", views.movie_list, name="movie-list"),
    path("my-bookings/", views.my_bookings, name="my-bookings"),
    path(
        "screenings/<int:screening_id>/seats/",
        views.seat_selection,
        name="seat-selection",
    ),
    path("seats/<int:seat_id>/reserve/", views.reserve_seat_view, name="reserve-seat"),
    path(
        "reservations/<int:reservation_id>/",
        views.reservation_confirmation,
        name="reservation-confirmation",
    ),
]
