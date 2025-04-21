from typing import NamedTuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings


class Middleware(NamedTuple):
    middleware_class: type
    kwargs: dict


def apply_middlewares(app: FastAPI, settings: Settings) -> None:
    app_middlewares: list[Middleware] = [
        Middleware(
            SessionMiddleware,
            {
                "secret_key": settings.secret_key,
                "https_only": settings.https_only,
            },
        ),
        Middleware(CORSMiddleware, {"allow_origins": ["*"]}),
    ]
    for middleware in app_middlewares:
        app.add_middleware(middleware.middleware_class, **middleware.kwargs)