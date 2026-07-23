from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, F
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PerformanceDetailSerializer,
    PerformanceListSerializer,
    PlayDetailSerializer,
    PlayListSerializer,
    ReservationSerializer,
    TheatreHallSerializer,
)


ACTOR_URL = reverse("theatre:actors-list")
GENRE_URL = reverse("theatre:genres-list")
PLAY_URL = reverse("theatre:plays-list")
THEATRE_HALL_URL = reverse("theatre:theatre-halls-list")
PERFORMANCE_URL = reverse("theatre:performances-list")
RESERVATION_URL = reverse("theatre:reservations-list")

ACTOR_DETAIL = "theatre:actors-detail"
GENRE_DETAIL = "theatre:genres-detail"
PLAY_DETAIL = "theatre:plays-detail"
THEATRE_HALL_DETAIL = "theatre:theatre-halls-detail"
PERFORMANCE_DETAIL = "theatre:performances-detail"
RESERVATION_DETAIL = "theatre:reservations-detail"


def sample_actor(**params):
    defaults = {
        "first_name": "John",
        "last_name": "Smith",
    }
    defaults.update(params)
    return Actor.objects.create(**defaults)


def sample_genre(**params):
    defaults = {"name": "Drama"}
    defaults.update(params)
    return Genre.objects.create(**defaults)


def sample_play(**params):
    actors = params.pop("actors", None)
    genres = params.pop("genres", None)
    defaults = {
        "title": "Hamlet",
        "description": "A theatre play",
    }
    defaults.update(params)
    play = Play.objects.create(**defaults)

    if actors:
        play.actors.set(actors)
    if genres:
        play.genres.set(genres)

    return play


def sample_theatre_hall(**params):
    defaults = {
        "name": "Main Hall",
        "rows": 10,
        "seats_in_row": 20,
    }
    defaults.update(params)
    return TheatreHall.objects.create(**defaults)


def sample_performance(**params):
    play = params.pop("play", None)
    theatre_hall = params.pop("theatre_hall", None)
    defaults = {
        "play": play or sample_play(),
        "theatre_hall": theatre_hall or sample_theatre_hall(),
        "show_time": timezone.now() + timedelta(days=1),
    }
    defaults.update(params)
    return Performance.objects.create(**defaults)


def sample_reservation(**params):
    user = params.pop("user", None)
    if user is None:
        user_number = get_user_model().objects.count()
        user = get_user_model().objects.create_user(
            email=f"reservation{user_number}@example.com",
            password="test-password",
        )
    defaults = {"user": user}
    defaults.update(params)
    return Reservation.objects.create(**defaults)


def sample_ticket(**params):
    performance = params.pop("performance", None)
    reservation = params.pop("reservation", None)
    defaults = {
        "row": 1,
        "seat": 1,
        "performance": performance or sample_performance(),
        "reservation": reservation or sample_reservation(),
    }
    defaults.update(params)
    return Ticket.objects.create(**defaults)


def detail_actor_url(actor):
    return reverse(ACTOR_DETAIL, args=[actor.id])


def detail_genre_url(genre):
    return reverse(GENRE_DETAIL, args=[genre.id])


def detail_play_url(play):
    return reverse(PLAY_DETAIL, args=[play.id])


def detail_theatre_hall_url(theatre_hall):
    return reverse(THEATRE_HALL_DETAIL, args=[theatre_hall.id])


def detail_performance_url(performance):
    return reverse(PERFORMANCE_DETAIL, args=[performance.id])


def detail_reservation_url(reservation):
    return reverse(RESERVATION_DETAIL, args=[reservation.id])


class UnauthenticatedTheatreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_actor_auth_required(self):
        response = self.client.get(ACTOR_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_genre_auth_required(self):
        response = self.client.get(GENRE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_play_auth_required(self):
        response = self.client.get(PLAY_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_theatre_hall_auth_required(self):
        response = self.client.get(THEATRE_HALL_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_performance_auth_required(self):
        response = self.client.get(PERFORMANCE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reservation_auth_required(self):
        response = self.client.get(RESERVATION_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTheatreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="test-password",
        )
        self.client.force_authenticate(self.user)
        self.actor = sample_actor()
        self.genre = sample_genre()
        self.play = sample_play(
            actors=[self.actor],
            genres=[self.genre],
        )
        self.hall = sample_theatre_hall()
        self.performance = sample_performance(
            play=self.play,
            theatre_hall=self.hall,
        )

    def test_actor_list(self):
        response = self.client.get(ACTOR_URL)
        actors = Actor.objects.order_by("first_name", "last_name")
        serializer = ActorSerializer(actors, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_actor_create_forbidden(self):
        payload = {"first_name": "Peter", "last_name": "Parker"}
        response = self.client.post(ACTOR_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_genre_list(self):
        response = self.client.get(GENRE_URL)
        genres = Genre.objects.order_by("name")
        serializer = GenreSerializer(genres, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_genre_create_forbidden(self):
        response = self.client.post(GENRE_URL, {"name": "Comedy"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_play_list_and_detail(self):
        list_response = self.client.get(PLAY_URL)
        list_serializer = PlayListSerializer(
            Play.objects.prefetch_related("actors", "genres"),
            many=True,
        )
        detail_response = self.client.get(detail_play_url(self.play))
        detail_serializer = PlayDetailSerializer(self.play)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list_response.data["results"],
            list_serializer.data,
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data, detail_serializer.data)

    def test_play_create_forbidden(self):
        payload = {
            "title": "New Play",
            "description": "Description",
            "actors": [self.actor.id],
            "genres": [self.genre.id],
        }
        response = self.client.post(PLAY_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_theatre_hall_list_and_capacity(self):
        response = self.client.get(THEATRE_HALL_URL)
        serializer = TheatreHallSerializer(
            TheatreHall.objects.order_by("name"),
            many=True,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)
        self.assertEqual(response.data["results"][0]["capacity"], 200)

    def test_theatre_hall_create_forbidden(self):
        payload = {
            "name": "Chamber Hall",
            "rows": 8,
            "seats_in_row": 12,
        }
        response = self.client.post(THEATRE_HALL_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_performance_list_and_detail(self):
        performances = (
            Performance.objects
            .select_related("play", "theatre_hall")
            .annotate(
                tickets_available=(
                    F("theatre_hall__rows")
                    * F("theatre_hall__seats_in_row")
                    - Count("tickets")
                )
            )
            .order_by("show_time", "id")
        )
        list_serializer = PerformanceListSerializer(
            performances,
            many=True,
        )
        list_response = self.client.get(PERFORMANCE_URL)
        detail_response = self.client.get(
            detail_performance_url(self.performance),
        )
        detailed_performance = performances.prefetch_related(
            "play__actors",
            "play__genres",
        ).get(id=self.performance.id)
        detail_serializer = PerformanceDetailSerializer(
            detailed_performance,
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list_response.data["results"],
            list_serializer.data,
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data, detail_serializer.data)

    def test_performance_create_forbidden(self):
        payload = {
            "play": self.play.id,
            "theatre_hall": self.hall.id,
            "show_time": (
                timezone.now() + timedelta(days=2)
            ).isoformat(),
        }
        response = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_actor_and_play_filters(self):
        second_actor = sample_actor(first_name="Jane", last_name="Doe")
        second_genre = sample_genre(name="Comedy")
        second_play = sample_play(
            title="New Comedy",
            actors=[second_actor],
            genres=[second_genre],
        )
        actor_response = self.client.get(
            ACTOR_URL,
            {"first_name": "jan", "last_name": "do"},
        )
        play_response = self.client.get(
            PLAY_URL,
            {
                "title": "comedy",
                "actors": second_actor.id,
                "genres": second_genre.id,
            },
        )

        self.assertEqual(
            {item["id"] for item in actor_response.data["results"]},
            {second_actor.id},
        )
        self.assertEqual(
            {item["id"] for item in play_response.data["results"]},
            {second_play.id},
        )

    def test_theatre_hall_and_performance_filters(self):
        second_hall = sample_theatre_hall(
            name="Chamber Hall",
            rows=5,
            seats_in_row=10,
        )
        second_play = sample_play(
            title="Macbeth",
            actors=[self.actor],
            genres=[self.genre],
        )
        second_performance = sample_performance(
            play=second_play,
            theatre_hall=second_hall,
            show_time=timezone.now() + timedelta(days=2),
        )
        hall_response = self.client.get(
            THEATRE_HALL_URL,
            {"min_capacity": 100},
        )
        performance_response = self.client.get(
            PERFORMANCE_URL,
            {
                "play": second_play.id,
                "theatre_hall": second_hall.id,
            },
        )

        self.assertEqual(
            {item["id"] for item in hall_response.data["results"]},
            {self.hall.id},
        )
        self.assertEqual(
            {
                item["id"]
                for item in performance_response.data["results"]
            },
            {second_performance.id},
        )

    def test_invalid_filters_return_bad_request(self):
        requests = (
            (PLAY_URL, {"actors": "invalid"}),
            (THEATRE_HALL_URL, {"min_capacity": "invalid"}),
            (THEATRE_HALL_URL, {"min_capacity": "0"}),
            (PERFORMANCE_URL, {"play": "invalid"}),
            (PERFORMANCE_URL, {"theatre_hall": "0"}),
        )

        for url, params in requests:
            with self.subTest(url=url, params=params):
                response = self.client.get(url, params)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_actor_list_is_paginated(self):
        for first_name in ("Alice", "Brenda", "Clara", "Diana", "Emma"):
            sample_actor(first_name=first_name, last_name="Jones")

        response = self.client.get(ACTOR_URL)

        self.assertEqual(response.data["count"], 6)
        self.assertEqual(len(response.data["results"]), 5)


class AdminTheatreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.client.force_authenticate(self.admin)
        self.actor = sample_actor()
        self.genre = sample_genre()
        self.play = sample_play(
            actors=[self.actor],
            genres=[self.genre],
        )
        self.hall = sample_theatre_hall()
        self.performance = sample_performance(
            play=self.play,
            theatre_hall=self.hall,
            show_time=timezone.now() + timedelta(days=2),
        )

    def test_actor_create_partial_update_and_delete(self):
        payload = {"first_name": "Peter", "last_name": "Parker"}
        create_response = self.client.post(ACTOR_URL, payload)
        actor = Actor.objects.get(id=create_response.data["id"])
        update_response = self.client.patch(
            detail_actor_url(actor),
            {"last_name": "Quill"},
        )
        delete_response = self.client.delete(detail_actor_url(actor))

        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["full_name"], "Peter Quill")
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_actor_validation_and_uniqueness(self):
        invalid_response = self.client.post(
            ACTOR_URL,
            {"first_name": "Invalid_Name", "last_name": "Smith"},
        )
        duplicate_response = self.client.post(
            ACTOR_URL,
            {"first_name": "john", "last_name": "smith"},
        )

        self.assertEqual(
            invalid_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_genre_create_update_and_delete(self):
        create_response = self.client.post(GENRE_URL, {"name": "Comedy"})
        genre = Genre.objects.get(id=create_response.data["id"])
        update_response = self.client.patch(
            detail_genre_url(genre),
            {"name": "Tragedy"},
        )
        duplicate_response = self.client.post(GENRE_URL, {"name": "drama"})
        delete_response = self.client.delete(detail_genre_url(genre))

        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_play_create_and_partial_update(self):
        payload = {
            "title": "New Play",
            "description": "Description",
            "actors": [self.actor.id],
            "genres": [self.genre.id],
        }
        create_response = self.client.post(PLAY_URL, payload)
        play = Play.objects.get(id=create_response.data["id"])
        update_response = self.client.patch(
            detail_play_url(play),
            {"description": "  Updated description  "},
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            update_response.data["description"],
            "Updated description",
        )

    def test_play_validations(self):
        payloads = (
            {
                "title": "Another Play",
                "description": "Description",
                "actors": [],
                "genres": [self.genre.id],
            },
            {
                "title": "Another Play",
                "description": "Description",
                "actors": [self.actor.id],
                "genres": [],
            },
            {
                "title": "Another Play",
                "description": "   ",
                "actors": [self.actor.id],
                "genres": [self.genre.id],
            },
            {
                "title": "Invalid_Title",
                "description": "Description",
                "actors": [self.actor.id],
                "genres": [self.genre.id],
            },
            {
                "title": "hamlet",
                "description": "Description",
                "actors": [self.actor.id],
                "genres": [self.genre.id],
            },
        )

        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post(PLAY_URL, payload)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_theatre_hall_create_and_capacity(self):
        payload = {
            "name": "Chamber Hall",
            "rows": 8,
            "seats_in_row": 12,
        }
        response = self.client.post(THEATRE_HALL_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["capacity"], 96)

    def test_theatre_hall_dimensions_cannot_be_updated(self):
        url = detail_theatre_hall_url(self.hall)
        name_response = self.client.patch(url, {"name": "Grand Hall"})
        rows_response = self.client.patch(url, {"rows": 11})
        seats_response = self.client.patch(url, {"seats_in_row": 21})

        self.assertEqual(name_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            rows_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            seats_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_theatre_hall_validations(self):
        payloads = (
            {"name": "   ", "rows": 1, "seats_in_row": 1},
            {"name": "Invalid123", "rows": 1, "seats_in_row": 1},
            {"name": "Small Hall", "rows": 0, "seats_in_row": 1},
            {"name": "main hall", "rows": 1, "seats_in_row": 1},
        )

        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post(THEATRE_HALL_URL, payload)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_performance_create(self):
        payload = {
            "play": self.play.id,
            "theatre_hall": self.hall.id,
            "show_time": (
                timezone.now() + timedelta(days=3)
            ).isoformat(),
        }
        response = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_past_and_duplicate_performances_are_rejected(self):
        past_payload = {
            "play": self.play.id,
            "theatre_hall": self.hall.id,
            "show_time": (
                timezone.now() - timedelta(days=1)
            ).isoformat(),
        }
        duplicate_payload = {
            "play": self.play.id,
            "theatre_hall": self.hall.id,
            "show_time": self.performance.show_time.isoformat(),
        }
        past_response = self.client.post(PERFORMANCE_URL, past_payload)
        duplicate_response = self.client.post(
            PERFORMANCE_URL,
            duplicate_payload,
        )

        self.assertEqual(
            past_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_performance_update_not_allowed(self):
        url = detail_performance_url(self.performance)
        put_response = self.client.put(url, {})
        patch_response = self.client.patch(url, {})

        self.assertEqual(
            put_response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            patch_response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_unbooked_performance_can_be_deleted(self):
        response = self.client.delete(
            detail_performance_url(self.performance),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_booked_objects_cannot_be_deleted(self):
        user = get_user_model().objects.create_user(
            email="customer@example.com",
            password="test-password",
        )
        reservation = sample_reservation(user=user)
        sample_ticket(
            performance=self.performance,
            reservation=reservation,
        )
        urls = (
            detail_performance_url(self.performance),
            detail_play_url(self.play),
            detail_theatre_hall_url(self.hall),
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.client.delete(url)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )


class ReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="test-password",
        )
        self.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.actor = sample_actor()
        self.genre = sample_genre()
        self.play = sample_play(
            actors=[self.actor],
            genres=[self.genre],
        )
        self.hall = sample_theatre_hall(rows=2, seats_in_row=3)
        self.future_performance = sample_performance(
            play=self.play,
            theatre_hall=self.hall,
            show_time=timezone.now() + timedelta(days=2),
        )
        self.past_performance = sample_performance(
            play=self.play,
            theatre_hall=self.hall,
            show_time=timezone.now() - timedelta(days=2),
        )

    def ticket_payload(self, row=1, seat=1, performance=None):
        if performance is None:
            performance = self.future_performance
        return {
            "performance": performance.id,
            "row": row,
            "seat": seat,
        }

    def test_reservation_create(self):
        self.client.force_authenticate(self.user)
        payload = {
            "user": self.other_user.email,
            "tickets": [
                self.ticket_payload(seat=1),
                self.ticket_payload(seat=2),
            ],
        }
        response = self.client.post(
            RESERVATION_URL,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], self.user.email)
        self.assertEqual(len(response.data["tickets"]), 2)
        reservation = Reservation.objects.get(id=response.data["id"])
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.tickets.count(), 2)

    def test_user_reservation_list(self):
        own_reservation = sample_reservation(user=self.user)
        sample_ticket(
            performance=self.future_performance,
            reservation=own_reservation,
            row=1,
            seat=1,
        )
        other_reservation = sample_reservation(user=self.other_user)
        sample_ticket(
            performance=self.future_performance,
            reservation=other_reservation,
            row=1,
            seat=2,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(RESERVATION_URL)
        reservations = (
            Reservation.objects
            .filter(user=self.user)
            .select_related("user")
            .prefetch_related("tickets")
        )
        serializer = ReservationSerializer(reservations, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_user_cannot_retrieve_another_users_reservation(self):
        reservation = sample_reservation(user=self.other_user)
        self.client.force_authenticate(self.user)
        response = self.client.get(detail_reservation_url(reservation))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_see_all_reservations(self):
        first_reservation = sample_reservation(user=self.user)
        second_reservation = sample_reservation(user=self.other_user)
        self.client.force_authenticate(self.admin)
        response = self.client.get(RESERVATION_URL)
        returned_ids = {
            item["id"] for item in response.data["results"]
        }

        self.assertEqual(
            returned_ids,
            {first_reservation.id, second_reservation.id},
        )

    def test_reservation_requires_ticket(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            RESERVATION_URL,
            {"tickets": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ticket_must_be_inside_hall(self):
        self.client.force_authenticate(self.user)
        payloads = (
            {"tickets": [self.ticket_payload(row=3)]},
            {"tickets": [self.ticket_payload(seat=4)]},
        )

        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    RESERVATION_URL,
                    payload,
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_ticket_for_past_performance_is_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            RESERVATION_URL,
            {
                "tickets": [
                    self.ticket_payload(
                        performance=self.past_performance,
                    ),
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_seat_cannot_be_selected_twice(self):
        self.client.force_authenticate(self.user)
        ticket = self.ticket_payload()
        response = self.client.post(
            RESERVATION_URL,
            {"tickets": [ticket, ticket]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_occupied_seat_does_not_create_partial_reservation(self):
        existing_reservation = sample_reservation(user=self.other_user)
        sample_ticket(
            performance=self.future_performance,
            reservation=existing_reservation,
            row=1,
            seat=1,
        )
        reservations_before = Reservation.objects.count()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            RESERVATION_URL,
            {
                "tickets": [
                    self.ticket_payload(row=2, seat=1),
                    self.ticket_payload(row=1, seat=1),
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), reservations_before)
        self.assertFalse(
            Ticket.objects.filter(
                performance=self.future_performance,
                row=2,
                seat=1,
            ).exists(),
        )

    def test_reservation_update_and_delete_not_allowed(self):
        reservation = sample_reservation(user=self.user)
        self.client.force_authenticate(self.user)
        url = detail_reservation_url(reservation)

        self.assertEqual(
            self.client.put(url, {"tickets": []}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.patch(url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.delete(url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
