"""ORM 模型单测：验证默认值、关系、级联删除。"""

from library.models.conversation import Conversation, Message


class TestConversationModel:
    def test_create_with_defaults(self, db_session):
        conv = Conversation()
        db_session.add(conv)
        db_session.commit()
        db_session.refresh(conv)

        assert conv.id  # UUID 自动生成
        assert len(conv.id) == 36
        assert conv.title == "New Conversation"
        assert conv.system_prompt is None
        assert conv.created_at is not None

    def test_create_with_custom_fields(self, db_session):
        conv = Conversation(title="八字咨询", system_prompt="你是八字大师。")
        db_session.add(conv)
        db_session.commit()
        db_session.refresh(conv)

        assert conv.title == "八字咨询"
        assert conv.system_prompt == "你是八字大师。"

    def test_cascade_delete_messages(self, db_session):
        conv = Conversation(title="t")
        db_session.add(conv)
        db_session.commit()

        msg = Message(conversation_id=conv.id, role="user", content="hi")
        db_session.add(msg)
        db_session.commit()

        db_session.delete(conv)
        db_session.commit()

        assert db_session.query(Message).count() == 0


class TestMessageModel:
    def test_optional_fields_default_none(self, db_session):
        conv = Conversation()
        db_session.add(conv)
        db_session.commit()

        msg = Message(conversation_id=conv.id, role="user", content="你好")
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.id
        assert msg.role == "user"
        assert msg.content == "你好"
        assert msg.thinking is None
        assert msg.input_tokens is None
        assert msg.output_tokens is None
        assert msg.thinking_duration_ms is None
        assert msg.total_duration_ms is None

    def test_relationship_back_populates(self, db_session):
        conv = Conversation()
        db_session.add(conv)
        db_session.commit()

        db_session.add_all([
            Message(conversation_id=conv.id, role="user", content="a"),
            Message(conversation_id=conv.id, role="assistant", content="b"),
        ])
        db_session.commit()
        db_session.refresh(conv)

        assert len(conv.messages) == 2
        assert {m.role for m in conv.messages} == {"user", "assistant"}
