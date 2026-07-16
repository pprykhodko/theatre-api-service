from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from theatre.models import *


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Actor
        fields =("id", "first_name", "last_name", "full_name")
        validators = [
            UniqueTogetherValidator(
                queryset=Actor.objects.all(),
                fields=("first_name", "last_name"),
                message="This actor already exists.",
            )
        ]

    def validate(self, attrs):
        for field_name in ("first_name", "last_name"):
            if field_name not in attrs:
                continue

            value = attrs[field_name].strip()

            if not value:
                raise serializers.ValidationError(
                    {
                        field_name: "This field must not be empty."
                    }
                )

            attrs[field_name] = value
        return attrs


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "This field must not be empty."
            )
        return value


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = (
            "id",
            "title",
            "description",
            "actors",
            "genres"
        )

    def validate(self, attrs):
        for field_name in ("title", "description"):
            if field_name not in attrs:
                continue

            value = attrs[field_name].strip()

            if not value:
                raise serializers.ValidationError(
                    {field_name: "This field must not be empty."}
                )

            attrs[field_name] = value

        if "actors" in attrs and not attrs["actors"]:
            raise serializers.ValidationError(
                {"actors": "At least one actor is required."}
            )

        if "genres" in attrs and not attrs["genres"]:
            raise serializers.ValidationError(
                {"genres": "At least one genre is required."}
            )

        return attrs


class PlayListSerializer(PlaySerializer):
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )


class PlayDetailSerializer(PlaySerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)


class TheatreHallsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHalls
        fields ="__all__"


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields ="__all__"


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields ="__all__"


class TickSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields ="__all__"
