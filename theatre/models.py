from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


actor_name_validator = RegexValidator(
    regex=r"^[^\W\d_]+(?:['-][^\W\d_]+)*$",
    message=(
        "Name may contain only letters, hyphens, and apostrophes."
    ),
)

genre_name_validator = RegexValidator(
    regex=r"^[^\W\d_]+(?:[ -][^\W\d_]+)*$",
    message="Genre name may contain only letters, spaces, and hyphens.",
)

play_title_validator = RegexValidator(
    regex=r"^[\w\s'\":;,.!?()&-]+$",
    message=(
        "Title contains invalid characters."
    ),
)


class Actor(models.Model):
    first_name = models.CharField(
        max_length=100,
        validators=[actor_name_validator]
    )
    last_name = models.CharField(
        max_length=100,
        validators=[actor_name_validator]
    )

    class Meta:
        ordering = ["first_name", "last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["first_name", "last_name"],
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
        unique=True,
        validators=[genre_name_validator]
    )

    class Meta:
        ordering = ["name"]

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

    def __str__(self) -> str:
        return self.title


class TheatreHalls(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rows = models.IntegerField()
    seats_in_rows = models.IntegerField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Performance(models.Model):
    play = models.ForeignKey(
        Play,
        on_delete=models.CASCADE,
        related_name="performances"
    )
    theatre_hall = models.ForeignKey(
        TheatreHalls,
        on_delete=models.CASCADE,
        related_name="performances"
    )
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["show_time"]

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
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(
        Performance,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    def __str__(self):
        return (
            f"{self.performance.play.title}: "
            f"row {self.row}, seat {self.seat}"
        )
