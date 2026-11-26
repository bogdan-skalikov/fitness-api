"""HTTP-слой: только разбор запроса и вызов сервиса."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import services
from app.db import get_db
from app.models import Training
from app.schemas import (
    BookingCreate,
    BookingDetailOut,
    BookingOut,
    ClientCreate,
    ClientOut,
    MembershipCreate,
    MembershipOut,
    TrainingCreate,
    TrainingOut,
)

router = APIRouter()


def _training_out(db: Session, training: Training) -> TrainingOut:
    return TrainingOut(
        id=training.id,
        title=training.title,
        starts_at=training.starts_at,
        capacity=training.capacity,
        booked=services.booked_count(db, training.id),
    )


@router.post(
    "/clients", response_model=ClientOut, status_code=status.HTTP_201_CREATED
)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> ClientOut:
    client = services.create_client(db, payload.full_name, payload.phone)
    return ClientOut.model_validate(client)


@router.get("/clients", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)) -> list[ClientOut]:
    return [ClientOut.model_validate(client) for client in services.list_clients(db)]


@router.get("/clients/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)) -> ClientOut:
    client = services.get_client(db, client_id)
    return ClientOut.model_validate(client)


@router.post(
    "/clients/{client_id}/memberships",
    response_model=MembershipOut,
    status_code=status.HTTP_201_CREATED,
)
def add_membership(
    client_id: int, payload: MembershipCreate, db: Session = Depends(get_db)
) -> MembershipOut:
    membership = services.add_membership(
        db,
        client_id=client_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        visits_total=payload.visits_total,
    )
    return MembershipOut.model_validate(membership)


@router.get("/clients/{client_id}/memberships", response_model=list[MembershipOut])
def list_memberships(
    client_id: int, db: Session = Depends(get_db)
) -> list[MembershipOut]:
    return [
        MembershipOut.model_validate(item)
        for item in services.list_memberships(db, client_id)
    ]


@router.post(
    "/trainings", response_model=TrainingOut, status_code=status.HTTP_201_CREATED
)
def create_training(
    payload: TrainingCreate, db: Session = Depends(get_db)
) -> TrainingOut:
    training = services.create_training(
        db,
        title=payload.title,
        starts_at=payload.starts_at,
        capacity=payload.capacity,
    )
    return _training_out(db, training)


@router.get("/trainings", response_model=list[TrainingOut])
def list_trainings(db: Session = Depends(get_db)) -> list[TrainingOut]:
    return [_training_out(db, item) for item in services.list_trainings(db)]


@router.post(
    "/trainings/{training_id}/bookings",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
)
def book_training(
    training_id: int, payload: BookingCreate, db: Session = Depends(get_db)
) -> BookingOut:
    booking = services.book_training(db, training_id, payload.client_id)
    return BookingOut.model_validate(booking)


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(booking_id: int, db: Session = Depends(get_db)) -> None:
    services.cancel_booking(db, booking_id)


@router.get("/bookings", response_model=list[BookingDetailOut])
def list_bookings(db: Session = Depends(get_db)) -> list[BookingDetailOut]:
    return [BookingDetailOut(**row) for row in services.list_bookings(db)]
