"""LLMStep 单测：
- 无 API Key 时走 mock 分支
- 有 API Key 时通过 mock httpx 客户端验证请求、响应解析、异常转换
"""

import json
from typing import Any

import httpx
import pytest

from library.base.exceptions import LLMException
from library.domain.step.llm_step import LLMStep, LLMUsage


# ── Mock 分支（无 API Key）──


class TestMockMode:
    async def test_call_llm_returns_mock_response(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "")
        step = LLMStep()

        reply, usage = await step.call_llm(
            [{"role": "user", "content": "你好"}]
        )

        assert "[Mock Response]" in reply
        assert "你好" in reply
        assert isinstance(usage, LLMUsage)
        assert usage.output_tokens == len(reply)

    async def test_call_llm_stream_emits_thinking_content_usage(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "")
        step = LLMStep()

        events: list[tuple[str, str]] = []
        async for ev in step.call_llm_stream(
            [{"role": "user", "content": "Q"}]
        ):
            events.append(ev)

        types = [t for t, _ in events]
        assert "thinking" in types
        assert "content" in types
        assert types[-1] == "usage"

        # usage 事件的 chunk 是合法 JSON
        usage_payload = json.loads(events[-1][1])
        assert {
            "input_tokens",
            "output_tokens",
            "thinking_duration_ms",
            "total_duration_ms",
        } <= set(usage_payload.keys())


# ── Real 分支：通过 httpx MockTransport 拦截请求 ──


def _install_mock_transport(monkeypatch, handler):
    """把 httpx.AsyncClient 替换成挂着 MockTransport 的版本。"""
    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    class _PatchedClient(original):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _PatchedClient)


class TestCallLLMWithKey:
    async def test_success_parses_reply_and_usage(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "sk-test")
        monkeypatch.setattr(
            "library.domain.step.llm_step.settings.llm_enable_thinking", False
        )

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            assert body["model"]
            assert body["messages"]
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": "hello from fake llm"}}
                    ],
                    "usage": {"prompt_tokens": 11, "completion_tokens": 22},
                },
            )

        _install_mock_transport(monkeypatch, handler)

        step = LLMStep()
        reply, usage = await step.call_llm(
            [{"role": "user", "content": "hi"}]
        )
        assert reply == "hello from fake llm"
        assert usage.input_tokens == 11
        assert usage.output_tokens == 22

    async def test_http_status_error_raises_llm_exception(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "sk-test")
        monkeypatch.setattr(
            "library.domain.step.llm_step.settings.llm_enable_thinking", False
        )

        def handler(_req: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="server error")

        _install_mock_transport(monkeypatch, handler)

        with pytest.raises(LLMException):
            await LLMStep().call_llm([{"role": "user", "content": "hi"}])

    async def test_timeout_raises_llm_exception(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "sk-test")
        monkeypatch.setattr(
            "library.domain.step.llm_step.settings.llm_enable_thinking", False
        )

        def handler(_req: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("slow")

        _install_mock_transport(monkeypatch, handler)

        with pytest.raises(LLMException) as exc_info:
            await LLMStep().call_llm([{"role": "user", "content": "hi"}])
        assert "超时" in exc_info.value.message

    async def test_connect_error_raises_llm_exception(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "sk-test")
        monkeypatch.setattr(
            "library.domain.step.llm_step.settings.llm_enable_thinking", False
        )

        def handler(_req: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("can't connect")

        _install_mock_transport(monkeypatch, handler)

        with pytest.raises(LLMException) as exc_info:
            await LLMStep().call_llm([{"role": "user", "content": "hi"}])
        assert "LLM" in exc_info.value.message

    async def test_bad_json_raises_llm_exception(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "sk-test")
        monkeypatch.setattr(
            "library.domain.step.llm_step.settings.llm_enable_thinking", False
        )

        def handler(_req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="not json")

        _install_mock_transport(monkeypatch, handler)

        with pytest.raises(LLMException):
            await LLMStep().call_llm([{"role": "user", "content": "hi"}])


class TestCallLLMStreamWithKey:
    async def test_stream_parses_sse_chunks(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "sk-test")
        monkeypatch.setattr(
            "library.domain.step.llm_step.settings.llm_enable_thinking", False
        )

        sse_body = (
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n'
            'data: {"choices":[{"delta":{"content":" World"}}]}\n'
            'data: {"choices":[{"delta":{}}],"usage":{"prompt_tokens":3,"completion_tokens":5}}\n'
            "data: [DONE]\n"
        )

        def handler(_req: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=sse_body.encode("utf-8"),
                headers={"content-type": "text/event-stream"},
            )

        _install_mock_transport(monkeypatch, handler)

        step = LLMStep()
        events = []
        async for ev in step.call_llm_stream(
            [{"role": "user", "content": "hi"}]
        ):
            events.append(ev)

        contents = [c for t, c in events if t == "content"]
        assert "".join(contents) == "Hello World"

        assert events[-1][0] == "usage"
        usage = json.loads(events[-1][1])
        assert usage["input_tokens"] == 3
        assert usage["output_tokens"] == 5

    async def test_stream_http_error_raises_llm_exception(self, monkeypatch):
        monkeypatch.setattr("library.domain.step.llm_step.settings.llm_api_key", "sk-test")
        monkeypatch.setattr(
            "library.domain.step.llm_step.settings.llm_enable_thinking", False
        )

        def handler(_req: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="boom")

        _install_mock_transport(monkeypatch, handler)

        with pytest.raises(LLMException):
            async for _ in LLMStep().call_llm_stream(
                [{"role": "user", "content": "hi"}]
            ):
                pass
