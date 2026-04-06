from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from library.base.exceptions import DatabaseException
from library.base.logger import logger
from library.models.conversation import Conversation, Message


class ConversationManager:
    def __init__(self, db: Session):
        self.db = db

    def _commit(self) -> None:
        """提交事务，失败时回滚并抛出 DatabaseException。"""
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("数据库提交失败: %s", str(exc))
            raise DatabaseException("数据库写入失败，请稍后重试")

    def create_conversation(self, title: str = "New Conversation") -> Conversation:
        conversation = Conversation(title=title)
        self.db.add(conversation)
        self._commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        try:
            return self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
        except SQLAlchemyError as exc:
            logger.error("查询会话失败: %s", str(exc))
            raise DatabaseException("数据库查询失败")

    def list_conversations(self) -> list[Conversation]:
        try:
            return (
                self.db.query(Conversation)
                .order_by(Conversation.updated_at.desc())
                .all()
            )
        except SQLAlchemyError as exc:
            logger.error("查询会话列表失败: %s", str(exc))
            raise DatabaseException("数据库查询失败")

    def update_conversation_title(self, conversation_id: str, title: str) -> Conversation | None:
        """更新会话标题，返回更新后的会话；会话不存在则返回 None。"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        try:
            conversation.title = title
            self._commit()
            self.db.refresh(conversation)
            return conversation
        except DatabaseException:
            raise
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("更新会话标题失败: %s", str(exc))
            raise DatabaseException("数据库写入失败，请稍后重试")

    def delete_conversation(self, conversation_id: str) -> bool:
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        self.db.delete(conversation)
        self._commit()
        return True

    def add_message(
        self, conversation_id: str, role: str, content: str
    ) -> Message:
        message = Message(
            conversation_id=conversation_id, role=role, content=content
        )
        self.db.add(message)
        self._commit()
        self.db.refresh(message)
        return message

    def get_messages(self, conversation_id: str) -> list[Message]:
        try:
            return (
                self.db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .all()
            )
        except SQLAlchemyError as exc:
            logger.error("查询消息列表失败: %s", str(exc))
            raise DatabaseException("数据库查询失败")
