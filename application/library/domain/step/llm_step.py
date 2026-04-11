"""Step 层：原子操作。

LLMStep 封装单次 LLM API 调用。这是领域层级的最底层——
phrase 层组合 step，但 step 不调用其他领域层。
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

import httpx

from config.settings import settings
from library.base.exceptions import LLMException
from library.base.llm_logger import log_llm_request
from library.base.logger import logger


class LLMStep:
    """原子步骤：向 LLM 发送消息并返回原始回复。"""

    async def call_llm(self, messages: list[dict]) -> str:
        """发送 chat-completion 请求并返回 assistant 内容（非流式）。"""
        request_id = uuid.uuid4().hex[:8]
        input_length = len(json.dumps(messages, ensure_ascii=False))
        start_time = datetime.now()

        if not settings.llm_api_key:
            reply = self._mock_response(messages)
            end_time = datetime.now()
            duration_s = (end_time - start_time).total_seconds() or 0.001
            log_llm_request(
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                input_length=input_length,
                output_length=len(reply),
                ttft_ms=duration_s * 1000,
                topt=len(reply) / duration_s,
                success=True,
                request_content=messages,
                response_content=reply,
            )
            return reply

        error_reason: str | None = None
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
            error_reason = "LLM 请求超时"
            logger.error(error_reason)
            self._log_failed(request_id, start_time, input_length, error_reason, messages)
            raise LLMException("LLM 请求超时，请稍后重试")
        except httpx.ConnectError:
            error_reason = f"无法连接 LLM 服务: {settings.llm_api_base_url}"
            logger.error(error_reason)
            self._log_failed(request_id, start_time, input_length, error_reason, messages)
            raise LLMException("无法连接 LLM 服务，请检查网络或服务地址配置")
        except httpx.HTTPStatusError as exc:
            error_reason = f"LLM 返回错误状态码: {exc.response.status_code} {exc.response.text[:200]}"
            logger.error(error_reason)
            self._log_failed(request_id, start_time, input_length, error_reason, messages)
            raise LLMException(f"LLM 服务返回错误 ({exc.response.status_code})")
        except httpx.HTTPError as exc:
            error_reason = f"LLM HTTP 请求异常: {str(exc)}"
            logger.error(error_reason)
            self._log_failed(request_id, start_time, input_length, error_reason, messages)
            raise LLMException("LLM 请求失败，请稍后重试")

        try:
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            error_reason = f"LLM 响应解析失败: {str(exc)}"
            logger.error("%s, 原始响应: %s", error_reason, response.text[:300])
            self._log_failed(request_id, start_time, input_length, error_reason, messages, response.text[:500])
            raise LLMException("LLM 响应格式异常，无法解析")

        # 成功日志
        end_time = datetime.now()
        duration_s = (end_time - start_time).total_seconds() or 0.001
        log_llm_request(
            request_id=request_id,
            start_time=start_time,
            end_time=end_time,
            input_length=input_length,
            output_length=len(reply),
            ttft_ms=duration_s * 1000,
            topt=len(reply) / duration_s,
            success=True,
            request_content=messages,
            response_content=reply,
        )
        return reply

    async def call_llm_stream(
        self, messages: list[dict]
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式调用 LLM，yield (event_type, chunk) 元组。

        event_type: "thinking" | "content"
        chunk: 增量文本片段
        """
        request_id = uuid.uuid4().hex[:8]
        input_length = len(json.dumps(messages, ensure_ascii=False))
        start_time = datetime.now()
        first_token_time: datetime | None = None

        if not settings.llm_api_key:
            # Mock 模式：模拟流式输出
            async for event_type, chunk in self._mock_stream(messages):
                if first_token_time is None:
                    first_token_time = datetime.now()
                yield event_type, chunk

            end_time = datetime.now()
            mock_reply = self._mock_response(messages)
            ttft = ((first_token_time or end_time) - start_time).total_seconds() * 1000
            duration_s = (end_time - start_time).total_seconds() or 0.001
            log_llm_request(
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                input_length=input_length,
                output_length=len(mock_reply),
                ttft_ms=ttft,
                topt=len(mock_reply) / duration_s,
                success=True,
                request_content=messages,
                response_content=mock_reply,
            )
            return

        full_thinking = ""
        full_content = ""

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
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
                        "stream": True,
                    },
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        error_reason = f"LLM 返回错误状态码: {response.status_code} {body.decode('utf-8', errors='replace')[:200]}"
                        logger.error(error_reason)
                        self._log_failed(request_id, start_time, input_length, error_reason, messages)
                        raise LLMException(f"LLM 服务返回错误 ({response.status_code})")

                    buffer = ""
                    async for raw_chunk in response.aiter_text():
                        buffer += raw_chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            if line == "data: [DONE]":
                                break
                            if not line.startswith("data: "):
                                continue

                            json_str = line[6:]
                            try:
                                data = json.loads(json_str)
                            except json.JSONDecodeError:
                                continue

                            delta = (
                                data.get("choices", [{}])[0]
                                .get("delta", {})
                            )

                            # 思考内容：reasoning_content（DeepSeek）
                            reasoning = delta.get("reasoning_content", "")
                            if reasoning:
                                if first_token_time is None:
                                    first_token_time = datetime.now()
                                full_thinking += reasoning
                                yield "thinking", reasoning

                            # 正式内容
                            content = delta.get("content", "")
                            if content:
                                if first_token_time is None:
                                    first_token_time = datetime.now()
                                full_content += content
                                yield "content", content

        except LLMException:
            raise
        except httpx.TimeoutException:
            error_reason = "LLM 流式请求超时"
            logger.error(error_reason)
            self._log_failed(request_id, start_time, input_length, error_reason, messages)
            raise LLMException("LLM 请求超时，请稍后重试")
        except httpx.ConnectError:
            error_reason = f"无法连接 LLM 服务: {settings.llm_api_base_url}"
            logger.error(error_reason)
            self._log_failed(request_id, start_time, input_length, error_reason, messages)
            raise LLMException("无法连接 LLM 服务，请检查网络或服务地址配置")
        except httpx.HTTPError as exc:
            error_reason = f"LLM 流式 HTTP 请求异常: {str(exc)}"
            logger.error(error_reason)
            self._log_failed(request_id, start_time, input_length, error_reason, messages)
            raise LLMException("LLM 请求失败，请稍后重试")

        # 成功日志
        end_time = datetime.now()
        ttft = ((first_token_time or end_time) - start_time).total_seconds() * 1000
        total_output = full_thinking + full_content
        duration_s = (end_time - start_time).total_seconds() or 0.001
        log_llm_request(
            request_id=request_id,
            start_time=start_time,
            end_time=end_time,
            input_length=input_length,
            output_length=len(total_output),
            ttft_ms=ttft,
            topt=len(total_output) / duration_s,
            success=True,
            request_content=messages,
            response_content=total_output,
        )

    @staticmethod
    async def _mock_stream(
        messages: list[dict],
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Mock 模式下模拟流式输出思考和内容。"""
        thinking_text = "[Mock 思考] 正在分析用户的问题..."
        for ch in thinking_text:
            yield "thinking", ch
            await asyncio.sleep(0.02)

        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        content_text = (
            f'[Mock Response] 收到你的消息: "{last_user_msg}"。'
            "请在 .env 中配置 LLM_API_KEY 以启用真实 LLM 响应。"
        )
        for ch in content_text:
            yield "content", ch
            await asyncio.sleep(0.02)

    @staticmethod
    def _log_failed(
        request_id: str,
        start_time: datetime,
        input_length: int,
        error_reason: str,
        messages: list[dict],
        raw_response: str | None = None,
    ) -> None:
        """记录失败的 LLM 请求日志。"""
        end_time = datetime.now()
        duration_s = (end_time - start_time).total_seconds() or 0.001
        log_llm_request(
            request_id=request_id,
            start_time=start_time,
            end_time=end_time,
            input_length=input_length,
            output_length=0,
            ttft_ms=duration_s * 1000,
            topt=0.0,
            success=False,
            error_reason=error_reason,
            request_content=messages,
            response_content=raw_response,
        )

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
