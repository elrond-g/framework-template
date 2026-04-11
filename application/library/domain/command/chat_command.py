"""Command layer: business command entry point.

ChatCommand expresses high-level business intent. It only calls Phrase layer —
never Step directly.
"""

from typing import AsyncGenerator

from library.domain.phrase.chat_phrase import ChatPhrase


class ChatCommand:
    """Command: process an incoming chat message and produce a reply."""

    def __init__(self):
        self.chat_phrase = ChatPhrase()

    async def execute(
        self,
        history: list[dict],
        user_message: str,
        system_prompt: str = "You are a helpful assistant.",
    ) -> str:
        """Execute the chat command (non-streaming).

        Delegates to ChatPhrase for the actual LLM interaction.
        """
        return await self.chat_phrase.generate_reply(
            history=history,
            user_message=user_message,
            system_prompt=system_prompt,
        )

    async def execute_stream(
        self,
        history: list[dict],
        user_message: str,
        system_prompt: str = "You are a helpful assistant.",
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Execute the chat command (streaming).

        yield (event_type, chunk) 元组。
        """
        async for event_type, chunk in self.chat_phrase.generate_reply_stream(
            history=history,
            user_message=user_message,
            system_prompt=system_prompt,
        ):
            yield event_type, chunk
