from django.contrib import admin

from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHalls,
    Performance,
    Reservation,
    Ticket
)

admin.site.register(Actor)
admin.site.register(Genre)
admin.site.register(Play)
admin.site.register(TheatreHalls)
admin.site.register(Performance)
admin.site.register(Reservation)
admin.site.register(Ticket)
