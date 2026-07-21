from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHall,
    Performance,
    Ticket,
    Reservation
)


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")

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

        if "title" in attrs:
            plays = Play.objects.filter(title__iexact=attrs["title"])

            if self.instance is not None:
                plays = plays.exclude(pk=self.instance.pk)

            if plays.exists():
                raise serializers.ValidationError({
                    "title": "This play already exists."
                })

        if "actors" in attrs and not attrs["actors"]:
            raise serializers.ValidationError({
                "actors": "At least one actor is required."
            })

        if "genres" in attrs and not attrs["genres"]:
            raise serializers.ValidationError({
                "genres": "At least one genre is required."
            })

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
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "capacity"
        )

    def validate(self, attrs):
        errors = {}

        if "name" in attrs:
            name = attrs["name"].strip()

            if not name:
                errors["name"] = "This field must not be empty."
            else:
                theatre_halls = TheatreHall.objects.filter(
                    name__iexact=name
                )
                if self.instance is not None:
                    theatre_halls = theatre_halls.exclude(
                        pk=self.instance.pk
                    )
                if theatre_halls.exists():
                    errors["name"] = "This hall already exists."

                attrs["name"] = name

        if self.instance is not None:
            rows = attrs.get("rows", self.instance.rows)
            seats_in_row = attrs.get(
                "seats_in_row",
                self.instance.seats_in_row
            )

            if rows != self.instance.rows:
                errors["rows"] = (
                    "The number of rows cannot be changed."
                )

            if seats_in_row != self.instance.seats_in_row:
                errors["seats_in_row"] = (
                    "The number of seats in a row cannot be changed."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class PerformanceSerializer(serializers.ModelSerializer):
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Performance
        fields = (
            "id",
            "play",
            "theatre_hall",
            "show_time",
            "tickets_available"
        )

    def validate_show_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Show time must be in the future."
            )
        return value


class PerformanceListSerializer(PerformanceSerializer):
    play = serializers.SlugRelatedField(
        read_only=True,
        slug_field="title"
    )
    theatre_hall = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )


class PerformanceDetailSerializer(PerformanceSerializer):
    play = PlayListSerializer(read_only=True)
    theatre_hall = TheatreHallSerializer(many=False, read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")
        read_only_fields = ("id",)

    def validate(self, attrs):
        performance = attrs.get(
            "performance",
            getattr(self.instance, "performance", None)
        )
        row = attrs.get("row", getattr(self.instance, "row", None))
        seat = attrs.get("seat", getattr(self.instance, "seat", None))

        theatre_hall = performance.theatre_hall

        if row < 1 or row > theatre_hall.rows:
            raise serializers.ValidationError({
                "row":
                    f"Row must be in range from 1 to {theatre_hall.rows}."
            })

        if seat < 1 or seat > theatre_hall.seats_in_row:
            raise serializers.ValidationError({
                "seat":
                    f"Seat must be in range from "
                    f"1 to {theatre_hall.seats_in_row}."
            })

        if performance.show_time <= timezone.now():
            raise serializers.ValidationError({
                "performance":
                    "Cannot book tickets for a past performance."
            })

        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        allow_empty=False
    )
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field="email"
    )

    class Meta:
        model = Reservation
        fields = ("id", "user", "tickets", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        tickets = attrs.get("tickets", [])
        selected_seats = set()

        for ticket in tickets:
            seat = (
                ticket["performance"].pk,
                ticket["row"],
                ticket["seat"],
            )

            if seat in selected_seats:
                raise serializers.ValidationError({
                    "tickets": "The same seat cannot be selected twice."
                })

            selected_seats.add(seat)

        return attrs

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")

        try:
            with transaction.atomic():
                reservation = Reservation.objects.create(**validated_data)

                Ticket.objects.bulk_create([
                    Ticket(reservation=reservation, **ticket_data)
                    for ticket_data in tickets_data
                ])

        except IntegrityError:
            raise serializers.ValidationError({
                "tickets": "One or more selected seats are already taken."
            })

        return reservation
