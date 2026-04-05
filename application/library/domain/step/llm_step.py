"""Step 层：原子操作。

LLMStep 封装单次 LLM API 调用。这是领域层级的最底层——
phrase 层组合 step，但 step 不调用其他领域层。
"""

import httpx

from config.settings import settings
from library.base.exceptions import LLMException
from library.base.logger import logger


class LLMStep:
    """原子步骤：向 LLM 发送消息并返回原始回复。"""

    async def call_llm(self, messages: list[dict]) -> str:
        """发送 chat-completion 请求并返回 assistant 内容。"""
        if not settings.llm_api_key:
            return self._mock_response(messages)

        try:
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
        except httpx.TimeoutException:
            logger.error("LLM 请求超时")
            raise LLMException("LLM 请求超时，请稍后重试")
        except httpx.ConnectError:
            logger.error("无法连接 LLM 服务: %s", settings.llm_api_base_url)
            raise LLMException("无法连接 LLM 服务，请检查网络或服务地址配置")
        except httpx.HTTPStatusError as exc:
            logger.error("LLM 返回错误状态码: %d %s", exc.response.status_code, exc.response.text[:200])
            raise LLMException(f"LLM 服务返回错误 ({exc.response.status_code})")
        except httpx.HTTPError as exc:
            logger.error("LLM HTTP 请求异常: %s", str(exc))
            raise LLMException("LLM 请求失败，请稍后重试")

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            logger.error("LLM 响应解析失败: %s, 原始响应: %s", str(exc), response.text[:300])
            raise LLMException("LLM 响应格式异常，无法解析")

    @staticmethod
    def _mock_response(messages: list[dict]) -> str:
        """API Key 未配置时返回占位响应。"""
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        return (
            f'[Mock Response] 收到你的消息: "{last_user_msg}"。'
            "请在 .env 中配置 LLM_API_KEY 以启用真实 LLM 响应。"
        )
