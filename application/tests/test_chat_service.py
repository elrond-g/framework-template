"""ChatService 单测：mock ChatCommand 以隔离 LLM。"""

import json
from unittest.mock import AsyncMock

import pytest

from library.base.exceptions import LLMException, NotFoundException
from library.domain.step.llm_step import LLMUsage
from library.services.chat_service import ChatService


def _patch_command(service: ChatService, reply: str = "assistant-reply",
                   usage: LLMUsage | None = None) -> AsyncMock:
    mock = AsyncMock(return_value=(reply, usage or LLMUsage(
        input_tokens=3, output_tokens=5, total_duration_ms=42
    )))
    service.chat_command.execute = mock  # type: ignore[assignment]
    return mock


def _patch_command_stream(service: ChatService, events: list[tuple[str, str]]):
    async def _stream(*, history, user_message, system_prompt):
        for ev in events:
            yield ev

    service.chat_command.execute_stream = _stream  # type: ignore[assignment]


class TestConversationCRUD:
    def test_create_conversation_normalizes_empty_prompt(self, db_session):
        svc = ChatService(db_session)

        data = svc.create_conversation(title="t", system_prompt="   ")
        assert data["title"] == "t"
        assert data["system_prompt"] is None

    def test_create_conversation_keeps_prompt(self, db_session):
        svc = ChatService(db_session)
        data = svc.create_conversation(title="t", system_prompt="  你好 ")
        # strip 后保留
        assert data["system_prompt"] == "你好"

    def test_list_conversations(self, db_session):
        svc = ChatService(db_session)
        svc.create_conversation(title="a")
        svc.create_conversation(title="b")
        items = svc.list_conversations()
        titles = [x["title"] for x in items]
        assert set(titles) == {"a", "b"}

    def test_update_conversation_title(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="old")
        updated = svc.update_conversation(c["id"], title="new")
        assert updated["title"] == "new"

    def test_update_missing_raises_not_found(self, db_session):
        svc = ChatService(db_session)
        with pytest.raises(NotFoundException):
            svc.update_conversation("x", title="new")

    def test_delete_missing_raises_not_found(self, db_session):
        svc = ChatService(db_session)
        with pytest.raises(NotFoundException):
            svc.delete_conversation("x")

    def test_delete_existing(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t")
        assert svc.delete_conversation(c["id"]) is True


class TestGetMessages:
    def test_missing_conversation_raises(self, db_session):
        svc = ChatService(db_session)
        with pytest.raises(NotFoundException):
            svc.get_conversation_messages("none")

    def test_returns_messages_with_optional_fields(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t")
        svc.manager.add_message(c["id"], role="user", content="q")
        svc.manager.add_message(
            c["id"], role="assistant", content="a",
            thinking="reasoning...", input_tokens=11,
            output_tokens=22, thinking_duration_ms=33, total_duration_ms=44,
        )

        msgs = svc.get_conversation_messages(c["id"])
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "q"
        # 可选字段仅在非空时出现
        assert "thinking" not in msgs[0]

        assert msgs[1]["thinking"] == "reasoning..."
        assert msgs[1]["input_tokens"] == 11
        assert msgs[1]["output_tokens"] == 22
        assert msgs[1]["thinking_duration_ms"] == 33
        assert msgs[1]["total_duration_ms"] == 44


class TestChatNonStream:
    async def test_missing_conversation_raises(self, db_session):
        svc = ChatService(db_session)
        with pytest.raises(NotFoundException):
            await svc.chat("nope", "hi")

    async def test_saves_user_and_assistant_and_usage(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t", system_prompt="自定义")
        _patch_command(svc, reply="hi-back", usage=LLMUsage(
            input_tokens=7, output_tokens=9, total_duration_ms=111
        ))

        result = await svc.chat(c["id"], "你好")
        assert result["role"] == "assistant"
        assert result["content"] == "hi-back"

        msgs = svc.manager.get_messages(c["id"])
        assert [m.role for m in msgs] == ["user", "assistant"]
        assert msgs[0].content == "你好"
        assert msgs[1].content == "hi-back"
        assert msgs[1].input_tokens == 7
        assert msgs[1].output_tokens == 9
        assert msgs[1].total_duration_ms == 111

    async def test_uses_custom_system_prompt_when_set(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t", system_prompt="定制提示")
        mock = _patch_command(svc)

        await svc.chat(c["id"], "hi")

        # Command 收到自定义 system_prompt
        assert mock.call_args.kwargs["system_prompt"] == "定制提示"

    async def test_llm_exception_saves_error_reply_then_reraises(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t")
        svc.chat_command.execute = AsyncMock(  # type: ignore[assignment]
            side_effect=LLMException("LLM 挂了")
        )

        with pytest.raises(LLMException):
            await svc.chat(c["id"], "hi")

        msgs = svc.manager.get_messages(c["id"])
        # user + 错误占位 assistant
        assert [m.role for m in msgs] == ["user", "assistant"]
        assert "LLM 挂了" in msgs[1].content


class TestChatStream:
    async def test_stream_accumulates_and_emits_done(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t")

        usage_payload = json.dumps({
            "input_tokens": 4, "output_tokens": 6,
            "thinking_duration_ms": 12, "total_duration_ms": 34,
        })
        _patch_command_stream(svc, [
            ("thinking", "思考..."),
            ("content", "你好"),
            ("content", "世界"),
            ("usage", usage_payload),
        ])

        raw_events = []
        async for line in svc.chat_stream(c["id"], "hi"):
            raw_events.append(line)

        # 每行是 "data: {json}\n\n"
        payloads = [json.loads(l[len("data: "):].strip()) for l in raw_events]
        types = [p["type"] for p in payloads]
        assert types[:3] == ["thinking", "content", "content"]
        # usage 事件不转发给客户端，最后是 done
        assert types[-1] == "done"
        assert "usage" not in types

        done = payloads[-1]
        assert done["input_tokens"] == 4
        assert done["output_tokens"] == 6
        assert done["thinking"] == "思考..."

        # 数据库中保存完整 content + thinking + usage
        msgs = svc.manager.get_messages(c["id"])
        assistant = msgs[-1]
        assert assistant.content == "你好世界"
        assert assistant.thinking == "思考..."
        assert assistant.input_tokens == 4
        assert assistant.output_tokens == 6

    async def test_stream_on_missing_conversation_emits_error(self, db_session):
        svc = ChatService(db_session)

        events = [l async for l in svc.chat_stream("nope", "hi")]
        assert len(events) == 1
        payload = json.loads(events[0][len("data: "):].strip())
        assert payload["type"] == "error"

    async def test_stream_llm_exception_saves_error_reply(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t")

        async def _raising(*, history, user_message, system_prompt):
            raise LLMException("streaming 挂了")
            yield  # pragma: no cover — make it an async generator

        svc.chat_command.execute_stream = _raising  # type: ignore[assignment]

        events = [l async for l in svc.chat_stream(c["id"], "hi")]
        last = json.loads(events[-1][len("data: "):].strip())
        assert last["type"] == "error"

        # 用户消息 + 错误占位 assistant 都落库
        msgs = svc.manager.get_messages(c["id"])
        assert [m.role for m in msgs] == ["user", "assistant"]
        assert "streaming 挂了" in msgs[1].content


class TestRetry:
    async def test_retry_missing_conversation_raises(self, db_session):
        svc = ChatService(db_session)
        with pytest.raises(NotFoundException):
            await svc.retry("none")

    async def test_retry_no_messages_raises(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t")
        with pytest.raises(NotFoundException):
            await svc.retry(c["id"])

    async def test_retry_deletes_last_assistant_and_regenerates(self, db_session):
        svc = ChatService(db_session)
        c = svc.create_conversation(title="t")
        svc.manager.add_message(c["id"], role="user", content="问题")
        svc.manager.add_message(c["id"], role="assistant", content="旧答案")

        _patch_command(svc, reply="新答案")

        result = await svc.retry(c["id"])
        assert result["content"] == "新答案"

        contents = [m.content for m in svc.manager.get_messages(c["id"])]
        assert "旧答案" not in contents
        assert "新答案" in contents

    async def test_retry_stream_missing_conversation_emits_error(self, db_session):
        svc = ChatService(db_session)
        events = [l async for l in svc.retry_stream("nope")]
        payload = json.loads(events[0][len("data: "):].strip())
        assert payload["type"] == "error"
