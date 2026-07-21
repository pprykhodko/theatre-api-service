from django.urls import path, include
from rest_framework import routers

from theatre.views import (
    ActorViewSet,
    PlayViewSet,
    GenreViewSet,
    TheatreHallViewSet,
    PerformanceViewSet,
    ReservationViewSet,
)

router = routers.DefaultRouter()

router.register("actors", ActorViewSet, basename="actors")
router.register("genres", GenreViewSet, basename="genres")
router.register("plays", PlayViewSet, basename="plays")
router.register(
    "theatre-halls",
    TheatreHallViewSet,
    basename="theatre-halls"
)
router.register(
    "performances",
    PerformanceViewSet,
    basename="performances"
)
router.register(
    "reservations",
    ReservationViewSet,
    basename="reservations"
)

urlpatterns = [path("", include(router.urls))]

app_name = "theatre"
