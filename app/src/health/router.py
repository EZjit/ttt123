from enum import Enum

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

health_router = APIRouter()


class HealthCheckResponse(str, Enum):
    OK = "OK"


@health_router.get("/ping", tags=["health"])
async def pong() -> JSONResponse:
    "Returns simple object"
    return JSONResponse({"ping": "pong!"})


@health_router.get(
    "/check",
    tags=["health"],
    response_class=PlainTextResponse,
)
async def check() -> HealthCheckResponse:
    "Returns plaint text"

    return HealthCheckResponse.OK