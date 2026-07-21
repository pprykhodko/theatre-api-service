from django.db.models import Count, F
from django.db.models.deletion import ProtectedError
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHall,
    Performance,
    Reservation,
)
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    TheatreHallSerializer,
    PerformanceSerializer,
    PerformanceListSerializer,
    PerformanceDetailSerializer,
    ReservationSerializer,
)


def _params_to_ints(value, param_name):
    try:
        ids = [int(item.strip()) for item in value.split(",")]
    except (TypeError, ValueError):
        raise serializers.ValidationError({
            param_name: "Enter comma-separated integer IDs."
        })

    if any(item <= 0 for item in ids):
        raise serializers.ValidationError({
            param_name: "IDs must be positive integers."
        })
    return ids


class ProtectBookedObjectDeletionMixin:
    protected_delete_message = (
        "This object cannot be deleted because tickets have already been sold."
    )

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError({
                "detail": self.protected_delete_message
            })


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class PlayViewSet(ProtectBookedObjectDeletionMixin, viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer

    def get_queryset(self):
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        queryset = super().get_queryset()

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genres_ids = _params_to_ints(genres, "genres")
            queryset = queryset.filter(genres__id__in=genres_ids)

        if actors:
            actors_ids = _params_to_ints(actors, "actors")
            queryset = queryset.filter(actors__id__in=actors_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        if self.action == "retrieve":
            return PlayDetailSerializer
        return PlaySerializer


class TheatreHallViewSet(
    ProtectBookedObjectDeletionMixin,
    viewsets.ModelViewSet,
):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class PerformanceViewSet(
    ProtectBookedObjectDeletionMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Performance.objects.select_related(
        "play",
        "theatre_hall"
    )
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action in ("list", "retrieve"):
            queryset = queryset.annotate(
                tickets_available=(
                    F("theatre_hall__rows")
                    * F("theatre_hall__seats_in_row")
                    - Count("tickets")
                )
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "play__actors",
                "play__genres"
            )

        play = self.request.query_params.get("play")
        theatre_hall = self.request.query_params.get("theatre_hall")

        if play:
            play_ids = _params_to_ints(play, "play")
            queryset = queryset.filter(play_id__in=play_ids)

        if theatre_hall:
            theatre_hall_ids = _params_to_ints(theatre_hall, "theatre_hall")
            queryset = queryset.filter(theatre_hall_id__in=theatre_hall_ids)

        return queryset.order_by("show_time", "pk")

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceDetailSerializer
        return PerformanceSerializer


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        Reservation.objects
        .select_related("user")
        .prefetch_related("tickets")
    )
    serializer_class = ReservationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
