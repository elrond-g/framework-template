"""Phrase layer: compose atomic steps into business logic fragments.

ChatPhrase builds the message payload and calls LLMStep.
Phrase only calls Step — never Command or Service.
"""

from library.domain.step.llm_step import LLMStep


class ChatPhrase:
    """Compose steps to produce an LLM-based chat reply."""

    def __init__(self):
        self.llm_step = LLMStep()

    async def generate_reply(
        self,
        history: list[dict],
        user_message: str,
        system_prompt: str = "You are a helpful assistant.",
    ) -> str:
        """Build the full message list and invoke the LLM step."""
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return await self.llm_step.call_llm(messages)
