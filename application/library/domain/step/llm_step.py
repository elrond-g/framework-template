"""Step layer: atomic operations.

LLMStep wraps a single LLM API call. This is the lowest level of the domain
hierarchy — phrase layer composes steps, but steps do not call other domain layers.
"""

import httpx

from config.settings import settings


class LLMStep:
    """Atomic step: send messages to an LLM and return the raw reply."""

    async def call_llm(self, messages: list[dict]) -> str:
        """Send a chat-completion request and return the assistant content."""
        if not settings.llm_api_key:
            return self._mock_response(messages)

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.llm_api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "max_tokens": settings.llm_max_tokens,
                    "temperature": settings.llm_temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _mock_response(messages: list[dict]) -> str:
        """Return a placeholder response when no API key is configured."""
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        return (
            f"[Mock Response] I received your message: \"{last_user_msg}\". "
            "Configure LLM_API_KEY in .env to enable real LLM responses."
        )
