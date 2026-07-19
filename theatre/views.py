from rest_framework import serializers, viewsets

from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHall, Performance
)
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    TheatreHallSerializer, PerformanceSerializer, PerformanceListSerializer, PerformanceDetailSerializer
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


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class PlayViewSet(viewsets.ModelViewSet):
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


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Performance.objects
        .select_related("play", "theatre_hall")
        .prefetch_related("play__actors", "play__genres")
    )
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        play = self.request.query_params.get("play")
        theatre_hall = self.request.query_params.get("theatre_hall")

        queryset = super().get_queryset()

        if play:
            plays_ids = _params_to_ints(play, "play")
            queryset = queryset.filter(play__id__in=plays_ids)

        if theatre_hall:
            theatre_hall_ids = _params_to_ints(theatre_hall, "theatre_hall")
            queryset = queryset.filter(theatre_hall__id__in=theatre_hall_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceDetailSerializer
        return PerformanceSerializer
