"""Точка входа приложения."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.db import Base, engine
from app.services import ApiError

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Для учебного проекта достаточно create_all; в реальном нужны миграции (Alembic).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Высота — API клуба",
    version="1.0.0",
    description="Запись в фитнес-клуб: клиенты, абонементы, тренировки.",
    lifespan=lifespan,
)

app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Панель клуба: обычный интерфейс вместо Swagger."""
    return FileResponse(STATIC_DIR / "index.html")


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok"}
