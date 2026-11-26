"""Схемы запросов и ответов (Pydantic v2)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ClientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=20)


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str


class MembershipCreate(BaseModel):
    start_date: date
    end_date: date
    visits_total: int = Field(default=8, gt=0, le=365)


class MembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    start_date: date
    end_date: date
    visits_left: int


class TrainingCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    starts_at: datetime
    capacity: int = Field(default=10, gt=0, le=500)


class TrainingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    starts_at: datetime
    capacity: int
    booked: int = 0


class BookingCreate(BaseModel):
    client_id: int


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    training_id: int
    client_id: int


class BookingDetailOut(BaseModel):
    """Запись для таблицы в интерфейсе: с именами вместо идентификаторов."""

    id: int
    client_id: int
    client_name: str
    training_id: int
    training_title: str
    starts_at: datetime
