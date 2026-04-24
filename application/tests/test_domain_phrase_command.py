"""Phrase 与 Command 层单测：验证其"组装消息、下沉调用"的职责。

由于 Phrase 必须调用 Step，Command 必须调用 Phrase，这里用 mock 隔离下层。
"""

from unittest.mock import AsyncMock

from library.domain.command.chat_command import ChatCommand
from library.domain.phrase.chat_phrase import ChatPhrase, SYSTEM_PROMPT
from library.domain.step.llm_step import LLMUsage


async def _consume(async_gen):
    return [item async for item in async_gen]


class TestChatPhrase:
    async def test_generate_reply_builds_messages_with_default_system_prompt(self):
        phrase = ChatPhrase()
        phrase.llm_step.call_llm = AsyncMock(return_value=("reply", LLMUsage()))

        history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
        ]
        reply, usage = await phrase.generate_reply(history, "q2")

        assert reply == "reply"
        assert isinstance(usage, LLMUsage)

        called_messages = phrase.llm_step.call_llm.call_args.args[0]
        assert called_messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
        assert called_messages[1:-1] == history
        assert called_messages[-1] == {"role": "user", "content": "q2"}

    async def test_generate_reply_custom_system_prompt(self):
        phrase = ChatPhrase()
        phrase.llm_step.call_llm = AsyncMock(return_value=("x", LLMUsage()))

        await phrase.generate_reply([], "hi", system_prompt="自定义系统提示")

        called = phrase.llm_step.call_llm.call_args.args[0]
        assert called[0]["role"] == "system"
        assert called[0]["content"] == "自定义系统提示"
        assert called[1] == {"role": "user", "content": "hi"}

    async def test_generate_reply_stream_forwards_chunks(self):
        phrase = ChatPhrase()

        async def _fake_stream(messages):
            assert messages[-1] == {"role": "user", "content": "hi"}
            yield "thinking", "t1"
            yield "content", "c1"
            yield "usage", '{"input_tokens":1}'

        phrase.llm_step.call_llm_stream = _fake_stream  # type: ignore[assignment]

        events = await _consume(phrase.generate_reply_stream([], "hi"))
        assert events == [
            ("thinking", "t1"),
            ("content", "c1"),
            ("usage", '{"input_tokens":1}'),
        ]


class TestChatCommand:
    async def test_execute_delegates_to_phrase(self):
        cmd = ChatCommand()
        cmd.chat_phrase.generate_reply = AsyncMock(
            return_value=("hi", LLMUsage(input_tokens=1, output_tokens=2))
        )

        reply, usage = await cmd.execute([], "q", system_prompt="sp")
        assert reply == "hi"
        assert usage.input_tokens == 1
        cmd.chat_phrase.generate_reply.assert_awaited_once_with(
            history=[], user_message="q", system_prompt="sp"
        )

    async def test_execute_stream_forwards_phrase_output(self):
        cmd = ChatCommand()

        async def _fake_stream(*, history, user_message, system_prompt):
            assert user_message == "q"
            yield "content", "a"
            yield "usage", "{}"

        cmd.chat_phrase.generate_reply_stream = _fake_stream  # type: ignore[assignment]

        events = await _consume(cmd.execute_stream([], "q"))
        assert events == [("content", "a"), ("usage", "{}")]
