from rest_framework import serializers
from theatre.models import *


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Actor
        fields =("id", "first_name", "last_name", "full_name")

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

        first_name = attrs.get(
            "first_name",
            getattr(self.instance, "first_name", None)
        )
        last_name = attrs.get(
            "last_name",
            getattr(self.instance, "last_name", None)
        )

        if first_name is not None and last_name is not None:
            actors = Actor.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
            )

            if self.instance is not None:
                actors = actors.exclude(pk=self.instance.pk)

            if actors.exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["This actor already exists."]}
                )
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

        genres = Genre.objects.filter(name__iexact=value)

        if self.instance is not None:
            genres = genres.exclude(pk=self.instance.pk)

        if genres.exists():
            raise serializers.ValidationError(
                "This genre already exists."
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


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "This field must not be empty."
            )

        theatre_hall = TheatreHall.objects.filter(name__iexact=value)

        if self.instance is not None:
            theatre_hall = theatre_hall.exclude(pk=self.instance.pk)

        if theatre_hall.exists():
            raise serializers.ValidationError(
                "This hall already exists."
            )

        return value


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
