from typing import Iterable, NamedTuple

from fastapi import APIRouter, FastAPI

from app.src.currency.router import currency_router
from app.src.delivery.router import delivery_router
from app.src.health.router import health_router

tags_metadata = [
    {
        "name": "health",
        "description": "Health check for api",
    },
    {
        "name": "api",
        "description": "Main delivery api logic",
    },
]


class Router(NamedTuple):
    router: APIRouter
    prefix: str


def apply_routes(app: FastAPI) -> None:
    api_routers: Iterable[Router] = (
        Router(health_router, "/health"),
        Router(currency_router, "/currency"),
        Router(delivery_router, "/delivery"),
    )
    api_router_v1 = APIRouter()

    for router in api_routers:
        api_router_v1.include_router(router.router, prefix=router.prefix)

    app.include_router(api_router_v1, prefix="/api/v1")