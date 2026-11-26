"""Тесты бизнес-правил записи на тренировку."""

from datetime import date, datetime, timedelta


def future(days: int = 1) -> str:
    moment = datetime.now() + timedelta(days=days)
    return moment.replace(microsecond=0).isoformat()


def create_client(client, phone: str = "+79000000001", name: str = "Иван Петров") -> int:
    response = client.post("/clients", json={"full_name": name, "phone": phone})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_training(client, capacity: int = 5, days: int = 1, title: str = "Йога") -> int:
    response = client.post(
        "/trainings",
        json={"title": title, "starts_at": future(days), "capacity": capacity},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_membership(
    client,
    client_id: int,
    visits: int = 5,
    start: date | None = None,
    end: date | None = None,
) -> dict:
    start = start or date.today()
    end = end or date.today() + timedelta(days=30)
    response = client.post(
        f"/clients/{client_id}/memberships",
        json={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "visits_total": visits,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def visits_left(client, client_id: int) -> int:
    response = client.get(f"/clients/{client_id}/memberships")
    assert response.status_code == 200, response.text
    return response.json()[0]["visits_left"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_duplicate_phone_conflict(client):
    create_client(client, phone="+79000000002")
    response = client.post(
        "/clients", json={"full_name": "Пётр Иванов", "phone": "+79000000002"}
    )
    assert response.status_code == 409


def test_booking_decrements_visits(client):
    client_id = create_client(client)
    training_id = create_training(client)
    create_membership(client, client_id, visits=5)

    response = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": client_id}
    )

    assert response.status_code == 201, response.text
    assert visits_left(client, client_id) == 4

    listed = client.get("/trainings").json()
    assert listed[0]["booked"] == 1


def test_second_booking_same_training_conflict(client):
    client_id = create_client(client)
    training_id = create_training(client)
    create_membership(client, client_id, visits=5)

    first = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": client_id}
    )
    assert first.status_code == 201, first.text

    second = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": client_id}
    )
    assert second.status_code == 409
    assert visits_left(client, client_id) == 4


def test_booking_without_membership_forbidden(client):
    client_id = create_client(client)
    training_id = create_training(client)

    response = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": client_id}
    )

    assert response.status_code == 403


def test_booking_with_expired_membership_forbidden(client):
    client_id = create_client(client)
    training_id = create_training(client)
    create_membership(
        client,
        client_id,
        visits=5,
        start=date.today() - timedelta(days=30),
        end=date.today() - timedelta(days=1),
    )

    response = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": client_id}
    )

    assert response.status_code == 403


def test_booking_without_visits_left_forbidden(client):
    client_id = create_client(client)
    training_id = create_training(client)
    create_membership(client, client_id, visits=1)

    assert (
        client.post(
            f"/trainings/{training_id}/bookings", json={"client_id": client_id}
        ).status_code
        == 201
    )

    another_training = create_training(client, title="Пилатес")
    response = client.post(
        f"/trainings/{another_training}/bookings", json={"client_id": client_id}
    )

    assert response.status_code == 403


def test_booking_when_full_conflict(client):
    training_id = create_training(client, capacity=1)

    first_client = create_client(client, phone="+79000000010")
    second_client = create_client(client, phone="+79000000011")
    create_membership(client, first_client, visits=5)
    create_membership(client, second_client, visits=5)

    first = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": first_client}
    )
    assert first.status_code == 201, first.text

    second = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": second_client}
    )
    assert second.status_code == 409


def test_booking_past_training_bad_request(client):
    client_id = create_client(client)
    training_id = create_training(client, days=-1)
    create_membership(client, client_id, visits=5)

    response = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": client_id}
    )

    assert response.status_code == 400


def test_cancel_returns_visit(client):
    client_id = create_client(client)
    training_id = create_training(client)
    create_membership(client, client_id, visits=5)

    booking = client.post(
        f"/trainings/{training_id}/bookings", json={"client_id": client_id}
    ).json()
    assert visits_left(client, client_id) == 4

    response = client.delete(f"/bookings/{booking['id']}")
    assert response.status_code == 204, response.text
    assert visits_left(client, client_id) == 5
    assert client.get("/trainings").json()[0]["booked"] == 0


def test_cancel_missing_booking_not_found(client):
    assert client.delete("/bookings/999").status_code == 404


def test_interface_page_in_russian(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Высота" in response.text
    assert "Тренировки" in response.text
    assert "Абонементы" in response.text


def test_clients_list(client):
    create_client(client, phone="+79000000020", name="Анна Сидорова")
    create_client(client, phone="+79000000021", name="Пётр Иванов")

    response = client.get("/clients")

    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()]
    assert names == ["Анна Сидорова", "Пётр Иванов"]


def test_bookings_list_has_names(client):
    client_id = create_client(client, phone="+79000000030")
    training_id = create_training(client, title="Стретчинг")
    create_membership(client, client_id, visits=3)

    client.post(f"/trainings/{training_id}/bookings", json={"client_id": client_id})

    response = client.get("/bookings")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["client_name"] == "Иван Петров"
    assert rows[0]["training_title"] == "Стретчинг"
    assert "starts_at" in rows[0]
