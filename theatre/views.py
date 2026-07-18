from rest_framework import serializers, viewsets

from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHall
)
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    TheatreHallSerializer
)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer

    @staticmethod
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

    def get_queryset(self):
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        queryset = super().get_queryset()

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genres_ids = self._params_to_ints(genres, "genres")
            queryset = queryset.filter(genres__id__in=genres_ids)

        if actors:
            actors_ids = self._params_to_ints(actors, "actors")
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
