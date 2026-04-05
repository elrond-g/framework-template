"""Command layer: business command entry point.

ChatCommand expresses high-level business intent. It only calls Phrase layer —
never Step directly.
"""

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
        """Execute the chat command.

        Delegates to ChatPhrase for the actual LLM interaction.
        """
        return await self.chat_phrase.generate_reply(
            history=history,
            user_message=user_message,
            system_prompt=system_prompt,
        )
