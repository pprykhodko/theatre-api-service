from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models.functions import Lower

from theatre.validators import (
    actor_last_name_validator,
    actor_name_validator,
    genre_name_validator,
    play_title_validator,
    theatre_hall_name_validator,
)


class Actor(models.Model):
    first_name = models.CharField(
        max_length=100,
        validators=[actor_name_validator]
    )
    last_name = models.CharField(
        max_length=100,
        validators=[actor_last_name_validator]
    )

    class Meta:
        ordering = ["first_name", "last_name"]
        constraints = [
            models.UniqueConstraint(
                Lower("first_name"),
                Lower("last_name"),
                name="unique_actor_full_name"
            )
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name


class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[genre_name_validator]
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_genre_name"
            )
        ]

    def __str__(self) -> str:
        return self.name


class Play(models.Model):
    title = models.CharField(
        max_length=255,
        validators=[play_title_validator]
    )
    description = models.TextField()
    actors = models.ManyToManyField(
        Actor,
        related_name="plays"
    )
    genres = models.ManyToManyField(
        Genre,
        related_name="plays"
    )

    class Meta:
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                Lower("title"),
                name="unique_play_title"
            )
        ]

    def __str__(self) -> str:
        return self.title


class TheatreHall(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[theatre_hall_name_validator]
    )
    rows = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    seats_in_row = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_theatre_hall_name"
            )
        ]

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Performance(models.Model):
    play = models.ForeignKey(
        Play,
        on_delete=models.CASCADE,
        related_name="performances"
    )
    theatre_hall = models.ForeignKey(
        TheatreHall,
        on_delete=models.CASCADE,
        related_name="performances"
    )
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["show_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["theatre_hall", "show_time"],
                name="unique_hall_performance"
            )
        ]

    def __str__(self):
        return f"{self.play.title} at {self.show_time}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pk} - {self.user}"


class Ticket(models.Model):
    row = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    seat = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    performance = models.ForeignKey(
        Performance,
        on_delete=models.PROTECT,
        related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["performance", "row", "seat"],
                name="unique_performance_seat"
            )
        ]

    def __str__(self):
        return (
            f"{self.performance.play.title}: "
            f"row {self.row}, seat {self.seat}"
        )
