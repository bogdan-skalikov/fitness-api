"""Подключение к базе: движок, фабрика сессий, базовый класс моделей."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fitness.db")

connect_args: dict = {}
engine_kwargs: dict = {}

if DATABASE_URL.startswith("sqlite"):
    # SQLite не любит обращения из разных потоков, а FastAPI работает в пуле потоков.
    connect_args = {"check_same_thread": False}
    if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
        # Одно общее соединение, иначе каждый запрос видит пустую базу.
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""


def get_db():
    """Зависимость FastAPI: сессия на время запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
