import sys
import os

# Ensure the application directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from library.base.exceptions import register_exception_handlers
from library.models.base import Base, engine
from controller.chat.chat_controller import router as chat_router
from controller.system.system_controller import router as system_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(chat_router)
    app.include_router(system_router)

    # Create database tables on startup
    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )
