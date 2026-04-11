"""Phrase 层：组合原子步骤为业务逻辑片段。

ChatPhrase 构建消息列表并调用 LLMStep。
Phrase 只调用 Step，不调用 Command 或 Service。
"""

from typing import AsyncGenerator

from library.domain.step.llm_step import LLMStep, LLMUsage

SYSTEM_PROMPT = "你是一位精通八字的大师。"


class ChatPhrase:
    """组合 step 生成基于 LLM 的聊天回复。"""

    def __init__(self):
        self.llm_step = LLMStep()

    async def generate_reply(
        self,
        history: list[dict],
        user_message: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> tuple[str, LLMUsage]:
        """构建完整消息列表并调用 LLM step（非流式）。返回 (回复内容, 统计数据)。"""
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return await self.llm_step.call_llm(messages)

    async def generate_reply_stream(
        self,
        history: list[dict],
        user_message: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """构建完整消息列表并流式调用 LLM step。

        yield (event_type, chunk) 元组，包括 "usage" 事件。
        """
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        async for event_type, chunk in self.llm_step.call_llm_stream(messages):
            yield event_type, chunk
