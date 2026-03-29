"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stock_adviser.api.routes.health import router as health_router
from stock_adviser.api.session import SessionStore


def create_app() -> FastAPI:
    app = FastAPI(title="Stock Adviser API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared session store — attached to app state so routes can access it
    app.state.sessions = SessionStore()

    app.include_router(health_router)

    return app
