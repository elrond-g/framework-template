"""异常体系单测：验证各异常的 code 映射、message，以及全局 handler 生效。"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from library.base.exceptions import (
    AppException,
    DatabaseException,
    LLMException,
    NotFoundException,
    ValidationException,
    register_exception_handlers,
)


class TestExceptionCodes:
    def test_app_exception_default(self):
        exc = AppException("something wrong")
        assert exc.message == "something wrong"
        assert exc.code == -1

    def test_not_found_code_404(self):
        exc = NotFoundException("会话不存在")
        assert exc.code == 404
        assert exc.message == "会话不存在"

    def test_validation_code_422(self):
        exc = ValidationException()
        assert exc.code == 422
        assert exc.message == "参数校验失败"

    def test_llm_code_502(self):
        exc = LLMException()
        assert exc.code == 502

    def test_database_code_500(self):
        exc = DatabaseException()
        assert exc.code == 500


class TestExceptionHandler:
    """以最小 FastAPI app 验证全局异常处理器工作。"""

    def _make_app(self) -> FastAPI:
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/not-found")
        def _nf():
            raise NotFoundException("bar 不存在")

        @app.get("/llm-fail")
        def _llm():
            raise LLMException("LLM 挂了")

        @app.get("/boom")
        def _boom():
            raise RuntimeError("意料之外")

        @app.get("/custom-code")
        def _custom():
            raise AppException("自定义", code=12345)

        return app

    def test_not_found_returns_404(self):
        with TestClient(self._make_app()) as client:
            resp = client.get("/not-found")
            assert resp.status_code == 404
            body = resp.json()
            assert body["code"] == 404
            assert body["message"] == "bar 不存在"
            assert body["data"] is None

    def test_llm_exception_returns_502(self):
        with TestClient(self._make_app()) as client:
            resp = client.get("/llm-fail")
            assert resp.status_code == 502
            assert resp.json()["code"] == 502

    def test_unknown_exception_returns_500(self):
        with TestClient(self._make_app(), raise_server_exceptions=False) as client:
            resp = client.get("/boom")
            assert resp.status_code == 500
            body = resp.json()
            assert body["code"] == 500
            assert "服务器内部错误" in body["message"]

    def test_custom_code_falls_back_to_400(self):
        """未在 _STATUS_CODE_MAP 中的 code 应回退到 HTTP 400。"""
        with TestClient(self._make_app()) as client:
            resp = client.get("/custom-code")
            assert resp.status_code == 400
            assert resp.json()["code"] == 12345
