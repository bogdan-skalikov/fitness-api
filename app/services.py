"""Бизнес-логика и доменные ошибки.

Роуты не знают правил — они только вызывают функции отсюда.
Так правила проверяются тестами отдельно от HTTP.
"""

from datetime import date, datetime

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Booking, Client, Membership, Training


class ApiError(Exception):
    """Ошибка предметной области: код ответа + человекочитаемое сообщение."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# --- Клиенты ---------------------------------------------------------------


def create_client(db: Session, full_name: str, phone: str) -> Client:
    if db.scalar(select(Client).where(Client.phone == phone)):
        raise ApiError(status.HTTP_409_CONFLICT, "Клиент с таким телефоном уже существует")

    client = Client(full_name=full_name, phone=phone)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def get_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Клиент не найден")
    return client


# --- Абонементы ------------------------------------------------------------


def add_membership(
    db: Session,
    client_id: int,
    start_date: date,
    end_date: date,
    visits_total: int,
) -> Membership:
    get_client(db, client_id)

    if end_date < start_date:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Дата окончания абонемента раньше даты начала",
        )

    membership = Membership(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        visits_left=visits_total,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def list_memberships(db: Session, client_id: int) -> list[Membership]:
    get_client(db, client_id)
    return list(
        db.scalars(
            select(Membership)
            .where(Membership.client_id == client_id)
            .order_by(Membership.start_date.desc())
        )
    )


# --- Тренировки ------------------------------------------------------------


def create_training(
    db: Session, title: str, starts_at: datetime, capacity: int
) -> Training:
    training = Training(title=title, starts_at=starts_at, capacity=capacity)
    db.add(training)
    db.commit()
    db.refresh(training)
    return training


def list_trainings(db: Session) -> list[Training]:
    return list(db.scalars(select(Training).order_by(Training.starts_at)))


def booked_count(db: Session, training_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Booking)
            .where(Booking.training_id == training_id)
        )
        or 0
    )


# --- Запись на тренировку --------------------------------------------------


def current_membership(db: Session, client_id: int, today: date) -> Membership | None:
    """Действующий на сегодня абонемент, без учёта остатка посещений."""
    return db.scalar(
        select(Membership)
        .where(
            Membership.client_id == client_id,
            Membership.start_date <= today,
            Membership.end_date >= today,
        )
        .order_by(Membership.end_date)
    )


def book_training(
    db: Session,
    training_id: int,
    client_id: int,
    now: datetime | None = None,
) -> Booking:
    now = now or datetime.now()

    training = db.get(Training, training_id)
    if training is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Тренировка не найдена")

    get_client(db, client_id)

    if training.starts_at <= now:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "Нельзя записаться на тренировку, которая уже началась",
        )

    already_booked = db.scalar(
        select(Booking).where(
            Booking.training_id == training_id,
            Booking.client_id == client_id,
        )
    )
    if already_booked is not None:
        raise ApiError(
            status.HTTP_409_CONFLICT, "Клиент уже записан на эту тренировку"
        )

    if booked_count(db, training_id) >= training.capacity:
        raise ApiError(status.HTTP_409_CONFLICT, "На тренировке нет свободных мест")

    membership = current_membership(db, client_id, now.date())
    if membership is None or membership.visits_left <= 0:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "Нет действующего абонемента с остатком посещений",
        )

    membership.visits_left -= 1
    booking = Booking(training_id=training_id, client_id=client_id)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def cancel_booking(db: Session, booking_id: int) -> None:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Запись не найдена")

    membership = current_membership(db, booking.client_id, date.today())
    if membership is not None:
        membership.visits_left += 1

    db.delete(booking)
    db.commit()


# --- Списки для интерфейса -------------------------------------------------


def list_clients(db: Session) -> list[Client]:
    return list(db.scalars(select(Client).order_by(Client.id)))


def list_bookings(db: Session) -> list[dict]:
    """Записи с именами клиента и тренировки — чтобы интерфейсу не дёргать лишнее."""
    rows = db.execute(
        select(Booking, Client.full_name, Training.title, Training.starts_at)
        .join(Client, Booking.client_id == Client.id)
        .join(Training, Booking.training_id == Training.id)
        .order_by(Training.starts_at, Booking.id)
    ).all()

    return [
        {
            "id": booking.id,
            "client_id": booking.client_id,
            "client_name": full_name,
            "training_id": booking.training_id,
            "training_title": title,
            "starts_at": starts_at,
        }
        for booking, full_name, title, starts_at in rows
    ]
