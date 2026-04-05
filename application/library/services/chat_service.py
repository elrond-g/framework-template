"""Service 层：编排 Manager 和领域 Command。

ChatService 由 Controller 调用，协调数据访问（Manager）和复杂业务逻辑（Command）。
不直接调用 phrase/step。
"""

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
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": str(m.created_at),
            }
            for m in messages
        ]

    def delete_conversation(self, conversation_id: str) -> bool:
        if not self.manager.delete_conversation(conversation_id):
            raise NotFoundException(f"会话 {conversation_id} 不存在")
        return True

    async def chat(self, conversation_id: str, user_message: str) -> dict:
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
            reply = await self.chat_command.execute(
                history=history,
                user_message=user_message,
            )
        except LLMException as exc:
            logger.warning("LLM 调用失败，会话 %s: %s", conversation_id, exc.message)
            # 保存一条错误提示作为 assistant 回复，保持对话完整性
            error_reply = f"[系统提示] {exc.message}"
            self.manager.add_message(
                conversation_id, role="assistant", content=error_reply
            )
            raise

        # 保存助手回复
        assistant_msg = self.manager.add_message(
            conversation_id, role="assistant", content=reply
        )

        return {
            "id": assistant_msg.id,
            "role": "assistant",
            "content": reply,
            "created_at": str(assistant_msg.created_at),
        }
