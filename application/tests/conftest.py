"""pytest 公共夹具：
- 将 application/ 加入 sys.path，测试代码可直接 `import library...`
- 默认把数据库切换为内存 SQLite，避免污染真实的 chatbot.db
- 关闭 LLM_API_KEY，使 LLMStep 走 mock 分支
- 提供内存数据库的 Session 夹具与 FastAPI TestClient 夹具
"""

import os
import sys

# 1. 路径：把 application/ 放到最前面，保证 `config`/`library` 可被导入
APPLICATION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APPLICATION_DIR not in sys.path:
    sys.path.insert(0, APPLICATION_DIR)

# 2. 环境变量：必须在导入应用模块之前设置，settings 是单例
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("LLM_API_KEY", "")
os.environ.setdefault("LOG_DIR", "logs")
os.environ.setdefault("DEBUG", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from library.models.base import Base


@pytest.fixture()
def db_engine():
    """每个测试函数使用独立的内存 SQLite 引擎，测试互不干扰。

    使用 StaticPool 让 TestClient 在不同线程中共享同一个 in-memory 连接，
    否则 FastAPI 在其他线程中拿到的是新的空库。
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """基于内存引擎的 Session。"""
    TestingSession = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_engine):
    """FastAPI TestClient：覆盖 get_db 依赖，让接口连接到内存数据库。"""
    from sqlalchemy.orm import sessionmaker
    from main import app
    from library.models.base import get_db

    TestingSession = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )

    def _override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
