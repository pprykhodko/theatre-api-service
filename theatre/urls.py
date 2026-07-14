from django.urls import path, include
from rest_framework import routers

from theatre.views import ActorViewSet, PlayViewSet, GenreViewSet

router = routers.DefaultRouter()

router.register("actors", ActorViewSet, basename="actors")
router.register("genres", GenreViewSet, basename="genres")
router.register("plays", PlayViewSet, basename="plays")

urlpatterns = [path("", include(router.urls))]

app_name = "theatre"
