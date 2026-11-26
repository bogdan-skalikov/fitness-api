"""Модели таблиц."""

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Client(Base):
    """Клиент клуба."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )


class Membership(Base):
    """Абонемент: срок действия и остаток посещений."""

    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    visits_left: Mapped[int] = mapped_column(nullable=False, default=0)

    client: Mapped["Client"] = relationship(back_populates="memberships")


class Training(Base):
    """Тренировка в расписании."""

    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False, default=10)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="training", cascade="all, delete-orphan"
    )


class Booking(Base):
    """Запись клиента на тренировку."""

    __tablename__ = "bookings"
    __table_args__ = (
        # Защита от двойной записи на уровне базы, а не только в коде.
        UniqueConstraint("training_id", "client_id", name="uq_booking_training_client"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    training_id: Mapped[int] = mapped_column(
        ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    training: Mapped["Training"] = relationship(back_populates="bookings")
    client: Mapped["Client"] = relationship(back_populates="bookings")
