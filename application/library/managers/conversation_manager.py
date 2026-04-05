from sqlalchemy.orm import Session

from library.models.conversation import Conversation, Message


class ConversationManager:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, title: str = "New Conversation") -> Conversation:
        conversation = Conversation(title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    def list_conversations(self) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def delete_conversation(self, conversation_id: str) -> bool:
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        self.db.delete(conversation)
        self.db.commit()
        return True

    def add_message(
        self, conversation_id: str, role: str, content: str
    ) -> Message:
        message = Message(
            conversation_id=conversation_id, role=role, content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(self, conversation_id: str) -> list[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
