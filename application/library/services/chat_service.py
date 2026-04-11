"""Service 层：编排 Manager 和领域 Command。

ChatService 由 Controller 调用，协调数据访问（Manager）和复杂业务逻辑（Command）。
不直接调用 phrase/step。
"""

import json
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from library.base.exceptions import LLMException, NotFoundException
from library.base.logger import logger
from library.domain.command.chat_command import ChatCommand
from library.managers.conversation_manager import ConversationManager


class ChatService:
    def __init__(self, db: Session):
        self.manager = ConversationManager(db)
        self.chat_command = ChatCommand()

    def create_conversation(self, title: str = "New Conversation") -> dict:
        conversation = self.manager.create_conversation(title=title)
        return {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": str(conversation.created_at),
        }

    def list_conversations(self) -> list[dict]:
        conversations = self.manager.list_conversations()
        return [
            {
                "id": c.id,
                "title": c.title,
                "created_at": str(c.created_at),
                "updated_at": str(c.updated_at),
            }
            for c in conversations
        ]

    def get_conversation_messages(self, conversation_id: str) -> list[dict]:
        conversation = self.manager.get_conversation(conversation_id)
        if not conversation:
            raise NotFoundException(f"会话 {conversation_id} 不存在")
        messages = self.manager.get_messages(conversation_id)
        result = []
        for m in messages:
            msg_dict = {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": str(m.created_at),
            }
            if m.thinking:
                msg_dict["thinking"] = m.thinking
            if m.input_tokens is not None:
                msg_dict["input_tokens"] = m.input_tokens
            if m.output_tokens is not None:
                msg_dict["output_tokens"] = m.output_tokens
            if m.thinking_duration_ms is not None:
                msg_dict["thinking_duration_ms"] = m.thinking_duration_ms
            if m.total_duration_ms is not None:
                msg_dict["total_duration_ms"] = m.total_duration_ms
            result.append(msg_dict)
        return result

    def update_conversation(self, conversation_id: str, title: str) -> dict:
        """更新会话标题。"""
        conversation = self.manager.update_conversation_title(conversation_id, title)
        if not conversation:
            raise NotFoundException(f"会话 {conversation_id} 不存在")
        return {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": str(conversation.created_at),
            "updated_at": str(conversation.updated_at),
        }

    def delete_conversation(self, conversation_id: str) -> bool:
        if not self.manager.delete_conversation(conversation_id):
            raise NotFoundException(f"会话 {conversation_id} 不存在")
        return True

    async def chat(self, conversation_id: str, user_message: str) -> dict:
        """非流式聊天（保留兼容）。"""
        conversation = self.manager.get_conversation(conversation_id)
        if not conversation:
            raise NotFoundException(f"会话 {conversation_id} 不存在")

        # 保存用户消息
        self.manager.add_message(conversation_id, role="user", content=user_message)

        # 构建历史消息
        messages = self.manager.get_messages(conversation_id)
        history = [
            {"role": m.role, "content": m.content}
            for m in messages[:-1]  # 排除刚添加的用户消息
        ]

        # 调用领域命令，捕获 LLM 异常避免半成品状态
        try:
            reply, usage = await self.chat_command.execute(
                history=history,
                user_message=user_message,
            )
        except LLMException as exc:
            logger.warning("LLM 调用失败，会话 %s: %s", conversation_id, exc.message)
            error_reply = f"[系统提示] {exc.message}"
            self.manager.add_message(
                conversation_id, role="assistant", content=error_reply
            )
            raise

        # 保存助手回复
        assistant_msg = self.manager.add_message(
            conversation_id, role="assistant", content=reply,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            thinking_duration_ms=usage.thinking_duration_ms,
            total_duration_ms=usage.total_duration_ms,
        )

        return {
            "id": assistant_msg.id,
            "role": "assistant",
            "content": reply,
            "created_at": str(assistant_msg.created_at),
        }

    async def chat_stream(
        self, conversation_id: str, user_message: str
    ) -> AsyncGenerator[str, None]:
        """流式聊天，yield SSE 格式行。"""
        conversation = self.manager.get_conversation(conversation_id)
        if not conversation:
            yield self._sse_error("会话不存在")
            return

        # 保存用户消息
        self.manager.add_message(conversation_id, role="user", content=user_message)

        # 构建历史消息
        messages = self.manager.get_messages(conversation_id)
        history = [
            {"role": m.role, "content": m.content}
            for m in messages[:-1]
        ]

        full_thinking = ""
        full_content = ""
        usage_data: dict = {}

        try:
            async for event_type, chunk in self.chat_command.execute_stream(
                history=history,
                user_message=user_message,
            ):
                if event_type == "thinking":
                    full_thinking += chunk
                    yield self._sse_event("thinking", chunk)
                elif event_type == "usage":
                    usage_data = json.loads(chunk)
                else:
                    full_content += chunk
                    yield self._sse_event(event_type, chunk)
        except LLMException as exc:
            logger.warning("流式 LLM 调用失败，会话 %s: %s", conversation_id, exc.message)
            error_reply = f"[系统提示] {exc.message}"
            self.manager.add_message(
                conversation_id, role="assistant", content=error_reply
            )
            yield self._sse_error(exc.message)
            return

        # 保存完整 assistant 回复（content + thinking + 统计数据）
        assistant_msg = self.manager.add_message(
            conversation_id, role="assistant", content=full_content,
            thinking=full_thinking or None,
            input_tokens=usage_data.get("input_tokens"),
            output_tokens=usage_data.get("output_tokens"),
            thinking_duration_ms=usage_data.get("thinking_duration_ms"),
            total_duration_ms=usage_data.get("total_duration_ms"),
        )

        yield self._sse_done(
            assistant_msg.id, str(assistant_msg.created_at),
            full_thinking, usage_data,
        )

    async def retry(self, conversation_id: str) -> dict:
        """非流式重试（保留兼容）。"""
        conversation = self.manager.get_conversation(conversation_id)
        if not conversation:
            raise NotFoundException(f"会话 {conversation_id} 不存在")

        self.manager.delete_last_assistant_message(conversation_id)

        messages = self.manager.get_messages(conversation_id)
        if not messages:
            raise NotFoundException("会话中没有可重试的消息")

        last_user_msg = None
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m
                break
        if not last_user_msg:
            raise NotFoundException("会话中没有用户消息，无法重试")

        history = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.id != last_user_msg.id
        ]

        try:
            reply, usage = await self.chat_command.execute(
                history=history,
                user_message=last_user_msg.content,
            )
        except LLMException as exc:
            logger.warning("重试 LLM 调用失败，会话 %s: %s", conversation_id, exc.message)
            error_reply = f"[系统提示] {exc.message}"
            self.manager.add_message(
                conversation_id, role="assistant", content=error_reply
            )
            raise

        assistant_msg = self.manager.add_message(
            conversation_id, role="assistant", content=reply,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            thinking_duration_ms=usage.thinking_duration_ms,
            total_duration_ms=usage.total_duration_ms,
        )

        return {
            "id": assistant_msg.id,
            "role": "assistant",
            "content": reply,
            "created_at": str(assistant_msg.created_at),
        }

    async def retry_stream(
        self, conversation_id: str
    ) -> AsyncGenerator[str, None]:
        """流式重试，yield SSE 格式行。"""
        conversation = self.manager.get_conversation(conversation_id)
        if not conversation:
            yield self._sse_error("会话不存在")
            return

        self.manager.delete_last_assistant_message(conversation_id)

        messages = self.manager.get_messages(conversation_id)
        if not messages:
            yield self._sse_error("会话中没有可重试的消息")
            return

        last_user_msg = None
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m
                break
        if not last_user_msg:
            yield self._sse_error("会话中没有用户消息，无法重试")
            return

        history = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.id != last_user_msg.id
        ]

        full_thinking = ""
        full_content = ""
        usage_data: dict = {}

        try:
            async for event_type, chunk in self.chat_command.execute_stream(
                history=history,
                user_message=last_user_msg.content,
            ):
                if event_type == "thinking":
                    full_thinking += chunk
                    yield self._sse_event("thinking", chunk)
                elif event_type == "usage":
                    usage_data = json.loads(chunk)
                else:
                    full_content += chunk
                    yield self._sse_event(event_type, chunk)
        except LLMException as exc:
            logger.warning("流式重试 LLM 调用失败，会话 %s: %s", conversation_id, exc.message)
            error_reply = f"[系统提示] {exc.message}"
            self.manager.add_message(
                conversation_id, role="assistant", content=error_reply
            )
            yield self._sse_error(exc.message)
            return

        assistant_msg = self.manager.add_message(
            conversation_id, role="assistant", content=full_content,
            thinking=full_thinking or None,
            input_tokens=usage_data.get("input_tokens"),
            output_tokens=usage_data.get("output_tokens"),
            thinking_duration_ms=usage_data.get("thinking_duration_ms"),
            total_duration_ms=usage_data.get("total_duration_ms"),
        )

        yield self._sse_done(
            assistant_msg.id, str(assistant_msg.created_at),
            full_thinking, usage_data,
        )

    # ── SSE 格式辅助方法 ──

    @staticmethod
    def _sse_event(event_type: str, content: str) -> str:
        payload = json.dumps({"type": event_type, "content": content}, ensure_ascii=False)
        return f"data: {payload}\n\n"

    @staticmethod
    def _sse_done(
        msg_id: str, created_at: str, thinking: str = "",
        usage_data: dict | None = None,
    ) -> str:
        payload_dict: dict = {
            "type": "done",
            "id": msg_id,
            "created_at": created_at,
            "thinking": thinking,
        }
        if usage_data:
            payload_dict["input_tokens"] = usage_data.get("input_tokens")
            payload_dict["output_tokens"] = usage_data.get("output_tokens")
            payload_dict["thinking_duration_ms"] = usage_data.get("thinking_duration_ms")
            payload_dict["total_duration_ms"] = usage_data.get("total_duration_ms")
        payload = json.dumps(payload_dict, ensure_ascii=False)
        return f"data: {payload}\n\n"

    @staticmethod
    def _sse_error(message: str) -> str:
        payload = json.dumps({"type": "error", "message": message}, ensure_ascii=False)
        return f"data: {payload}\n\n"
