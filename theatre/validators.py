from django.core.validators import RegexValidator


actor_name_validator = RegexValidator(
    regex=r"^[^\W\d_]+(?:['-][^\W\d_]+)*$",
    message=(
        "Name may contain only letters, hyphens, and apostrophes."
    ),
)

actor_last_name_validator = RegexValidator(
    regex=r"^[^\W\d_]+(?:[ '-][^\W\d_]+)*$",
    message=(
        "Last name may contain only letters, spaces, hyphens, "
        "and apostrophes."
    ),
)

genre_name_validator = RegexValidator(
    regex=r"^[^\W\d_]+(?:[ -][^\W\d_]+)*$",
    message="Genre name may contain only letters, spaces, and hyphens.",
)

play_title_validator = RegexValidator(
    regex=r"^[^\W\d_]+(?: [^\W\d_]+)*$",
    message="Title may contain only letters and single spaces.",
)

theatre_hall_name_validator = RegexValidator(
    regex=r"^[^\W\d_]+(?:[ '-][^\W\d_]+)*$",
    message="Theatre hall name may contain only "
            "letters, spaces, hyphens and apostrophes.",
)
