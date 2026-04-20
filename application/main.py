import sys
import os

# Ensure the application directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from config.settings import settings
from library.base.exceptions import register_exception_handlers
from library.base.logger import logger
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
        _migrate_conversations_add_system_prompt()

    return app


def _migrate_conversations_add_system_prompt() -> None:
    """轻量迁移：为老版本 DB 补齐 conversations.system_prompt 列（幂等）。"""
    try:
        inspector = inspect(engine)
        if "conversations" not in inspector.get_table_names():
            return
        columns = {c["name"] for c in inspector.get_columns("conversations")}
        if "system_prompt" in columns:
            return
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE conversations ADD COLUMN system_prompt TEXT"))
        logger.info("已为 conversations 表新增 system_prompt 列")
    except Exception as exc:
        logger.error("迁移 conversations.system_prompt 失败: %s", exc)


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )
