"""ApiResponse 单测：验证 success / error 两个工厂方法。"""

from library.base.api_response import ApiResponse


class TestApiResponse:
    def test_success_default(self):
        resp = ApiResponse.success()
        assert resp.code == 0
        assert resp.message == "success"
        assert resp.data is None

    def test_success_with_data(self):
        resp = ApiResponse.success(data={"foo": "bar"}, message="ok")
        assert resp.code == 0
        assert resp.message == "ok"
        assert resp.data == {"foo": "bar"}

    def test_error_default_code(self):
        resp = ApiResponse.error(message="boom")
        assert resp.code == -1
        assert resp.message == "boom"
        assert resp.data is None

    def test_error_custom_code(self):
        resp = ApiResponse.error(message="not found", code=404)
        assert resp.code == 404
        assert resp.message == "not found"

    def test_model_dump_roundtrip(self):
        resp = ApiResponse.success(data=[1, 2, 3])
        dumped = resp.model_dump()
        assert dumped == {"code": 0, "message": "success", "data": [1, 2, 3]}
