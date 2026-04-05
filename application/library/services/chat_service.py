"""Service layer: orchestrate managers and domain commands.

ChatService is called by controllers. It coordinates data access (managers)
and complex business logic (domain commands). It never calls phrase/step directly.
"""

from sqlalchemy.orm import Session

from library.base.exceptions import NotFoundException
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
            raise NotFoundException(f"Conversation {conversation_id} not found")
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
            raise NotFoundException(f"Conversation {conversation_id} not found")
        return True

    async def chat(self, conversation_id: str, user_message: str) -> dict:
        conversation = self.manager.get_conversation(conversation_id)
        if not conversation:
            raise NotFoundException(f"Conversation {conversation_id} not found")

        # Save user message
        self.manager.add_message(conversation_id, role="user", content=user_message)

        # Build history from stored messages
        messages = self.manager.get_messages(conversation_id)
        history = [
            {"role": m.role, "content": m.content}
            for m in messages[:-1]  # exclude the just-added user message
        ]

        # Delegate to domain command
        reply = await self.chat_command.execute(
            history=history,
            user_message=user_message,
        )

        # Save assistant reply
        assistant_msg = self.manager.add_message(
            conversation_id, role="assistant", content=reply
        )

        return {
            "id": assistant_msg.id,
            "role": "assistant",
            "content": reply,
            "created_at": str(assistant_msg.created_at),
        }
