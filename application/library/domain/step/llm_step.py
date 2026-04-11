"""Step 层：原子操作。

LLMStep 封装单次 LLM API 调用。这是领域层级的最底层——
phrase 层组合 step，但 step 不调用其他领域层。
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import AsyncGenerator

import httpx

from config.settings import settings
from library.base.exceptions import LLMException
from library.base.llm_logger import log_llm_request
from library.base.logger import logger


@dataclass
class LLMUsage:
    """LLM 调用的统计数据。"""
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_duration_ms: int = 0
    total_duration_ms: int = 0


class LLMStep:
    """原子步骤：向 LLM 发送消息并返回原始回复。"""

    async def call_llm(self, messages: list[dict]) -> tuple[str, LLMUsage]:
        """发送 chat-completion 请求并返回 (assistant 内容, 统计数据)（非流式）。"""
        request_id = uuid.uuid4().hex[:8]
        input_length = len(json.dumps(messages, ensure_ascii=False))
        start_time = datetime.now()

        if not settings.llm_api_key:
            reply = self._mock_response(messages)
            end_time = datetime.now()
            duration_s = (end_time - start_time).total_seconds() or 0.001
            total_duration_ms = int((end_time - start_time).total_seconds() * 1000)
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
            usage = LLMUsage(
                input_tokens=input_length,
                output_tokens=len(reply),
                thinking_duration_ms=0,
                total_duration_ms=total_duration_ms,
            )
            return reply, usage

        error_reason: str | None = None
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                request_body = {
                    "model": settings.llm_model,
                    "messages": messages,
                    "max_tokens": settings.llm_max_tokens,
                    "temperature": settings.llm_temperature,
                }
                if settings.llm_enable_thinking:
                    request_body["reasoning_effort"] = "high"
                    request_body["enable_thinking"] = True
                    request_body["thinking"] = {
                        "budget_tokens": settings.llm_thinking_budget_tokens,
                    }

                response = await client.post(
                    f"{settings.llm_api_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_body,
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

        # 提取 usage 统计
        end_time = datetime.now()
        total_duration_ms = int((end_time - start_time).total_seconds() * 1000)
        api_usage = data.get("usage", {})
        usage = LLMUsage(
            input_tokens=api_usage.get("prompt_tokens", 0),
            output_tokens=api_usage.get("completion_tokens", 0),
            thinking_duration_ms=0,
            total_duration_ms=total_duration_ms,
        )

        # 成功日志
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
        return reply, usage

    async def call_llm_stream(
        self, messages: list[dict]
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式调用 LLM，yield (event_type, chunk) 元组。

        event_type: "thinking" | "content" | "usage"
        chunk: 增量文本片段，usage 类型时为 JSON 字符串
        """
        request_id = uuid.uuid4().hex[:8]
        input_length = len(json.dumps(messages, ensure_ascii=False))
        start_time = datetime.now()
        first_token_time: datetime | None = None
        first_content_time: datetime | None = None

        if not settings.llm_api_key:
            # Mock 模式：模拟流式输出
            async for event_type, chunk in self._mock_stream(messages):
                if first_token_time is None:
                    first_token_time = datetime.now()
                if event_type == "content" and first_content_time is None:
                    first_content_time = datetime.now()
                yield event_type, chunk

            end_time = datetime.now()
            mock_reply = self._mock_response(messages)
            ttft = ((first_token_time or end_time) - start_time).total_seconds() * 1000
            duration_s = (end_time - start_time).total_seconds() or 0.001
            total_duration_ms = int((end_time - start_time).total_seconds() * 1000)
            thinking_duration_ms = int(((first_content_time or end_time) - start_time).total_seconds() * 1000)
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
            usage = LLMUsage(
                input_tokens=input_length,
                output_tokens=len(mock_reply),
                thinking_duration_ms=thinking_duration_ms,
                total_duration_ms=total_duration_ms,
            )
            yield "usage", json.dumps(asdict(usage), ensure_ascii=False)
            return

        full_thinking = ""
        full_content = ""
        stream_usage: dict = {}

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                request_body = {
                    "model": settings.llm_model,
                    "messages": messages,
                    "max_tokens": settings.llm_max_tokens,
                    "temperature": settings.llm_temperature,
                    "stream": True,
                    "stream_options": {"include_usage": True},
                }
                if settings.llm_enable_thinking:
                    request_body["reasoning_effort"] = "high"
                    request_body["enable_thinking"] = True
                    request_body["thinking"] = {
                        "budget_tokens": settings.llm_thinking_budget_tokens,
                    }

                async with client.stream(
                    "POST",
                    f"{settings.llm_api_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_body,
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

                            # 提取流式 usage（最后一个 chunk 包含）
                            chunk_usage = data.get("usage")
                            if chunk_usage:
                                stream_usage = chunk_usage

                            delta = (
                                data.get("choices", [{}])[0]
                                .get("delta", {})
                            )

                            # 调试：打印原始 delta 字段，排查 thinking 字段名
                            if delta:
                                logger.debug("SSE delta keys=%s, delta=%s", list(delta.keys()), str(delta)[:200])

                            # 思考内容：兼容多种字段名
                            # - reasoning_content: DeepSeek / 部分 new-api 代理
                            # - reasoning: OpenRouter 等代理
                            reasoning = (
                                delta.get("reasoning_content", "")
                                or delta.get("reasoning", "")
                            )
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
                                if first_content_time is None:
                                    first_content_time = datetime.now()
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

        # 构建统计数据并 yield usage 事件
        total_duration_ms = int((end_time - start_time).total_seconds() * 1000)
        thinking_duration_ms = int(((first_content_time or end_time) - start_time).total_seconds() * 1000) if full_thinking else 0
        usage = LLMUsage(
            input_tokens=stream_usage.get("prompt_tokens", 0),
            output_tokens=stream_usage.get("completion_tokens", 0),
            thinking_duration_ms=thinking_duration_ms,
            total_duration_ms=total_duration_ms,
        )
        yield "usage", json.dumps(asdict(usage), ensure_ascii=False)

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
