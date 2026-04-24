"""ConversationManager 单测：覆盖增删改查与异常路径。"""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from library.base.exceptions import DatabaseException
from library.managers.conversation_manager import ConversationManager


class TestCreateConversation:
    def test_create_default(self, db_session):
        mgr = ConversationManager(db_session)
        conv = mgr.create_conversation()
        assert conv.id
        assert conv.title == "New Conversation"
        assert conv.system_prompt is None

    def test_create_with_system_prompt(self, db_session):
        mgr = ConversationManager(db_session)
        conv = mgr.create_conversation(title="八字", system_prompt="你是大师。")
        assert conv.title == "八字"
        assert conv.system_prompt == "你是大师。"


class TestQueryConversation:
    def test_get_conversation_found(self, db_session):
        mgr = ConversationManager(db_session)
        created = mgr.create_conversation(title="a")
        got = mgr.get_conversation(created.id)
        assert got is not None
        assert got.id == created.id

    def test_get_conversation_missing_returns_none(self, db_session):
        mgr = ConversationManager(db_session)
        assert mgr.get_conversation("not-exist") is None

    def test_list_conversations_order_by_updated_desc(self, db_session):
        from datetime import datetime, timedelta

        mgr = ConversationManager(db_session)
        c1 = mgr.create_conversation(title="first")
        c2 = mgr.create_conversation(title="second")
        # SQLite func.now() 秒级精度，手动错开 updated_at 以验证排序
        c1.updated_at = datetime.now() - timedelta(seconds=10)
        c2.updated_at = datetime.now()
        db_session.commit()

        items = mgr.list_conversations()
        assert items[0].id == c2.id
        assert items[1].id == c1.id


class TestUpdateAndDelete:
    def test_update_title(self, db_session):
        mgr = ConversationManager(db_session)
        conv = mgr.create_conversation(title="old")
        updated = mgr.update_conversation_title(conv.id, "new")
        assert updated is not None
        assert updated.title == "new"

    def test_update_title_missing_returns_none(self, db_session):
        mgr = ConversationManager(db_session)
        assert mgr.update_conversation_title("not-exist", "x") is None

    def test_delete_existing(self, db_session):
        mgr = ConversationManager(db_session)
        conv = mgr.create_conversation()
        assert mgr.delete_conversation(conv.id) is True
        assert mgr.get_conversation(conv.id) is None

    def test_delete_missing_returns_false(self, db_session):
        mgr = ConversationManager(db_session)
        assert mgr.delete_conversation("not-exist") is False


class TestMessages:
    def test_add_and_get_messages_ordered(self, db_session):
        mgr = ConversationManager(db_session)
        conv = mgr.create_conversation()

        mgr.add_message(conv.id, role="user", content="q1")
        mgr.add_message(
            conv.id, role="assistant", content="a1",
            thinking="t", input_tokens=10, output_tokens=20,
            thinking_duration_ms=100, total_duration_ms=200,
        )

        msgs = mgr.get_messages(conv.id)
        assert [m.content for m in msgs] == ["q1", "a1"]
        assert msgs[1].thinking == "t"
        assert msgs[1].input_tokens == 10
        assert msgs[1].output_tokens == 20
        assert msgs[1].thinking_duration_ms == 100
        assert msgs[1].total_duration_ms == 200

    def test_delete_last_assistant_message(self, db_session):
        from datetime import datetime, timedelta

        mgr = ConversationManager(db_session)
        conv = mgr.create_conversation()
        m_q1 = mgr.add_message(conv.id, role="user", content="q1")
        m_a1 = mgr.add_message(conv.id, role="assistant", content="a1")
        m_q2 = mgr.add_message(conv.id, role="user", content="q2")
        m_a2 = mgr.add_message(conv.id, role="assistant", content="a2")

        # SQLite func.now() 秒级精度：手工给每条消息错开时间戳，
        # 保证 "最后一条 assistant" 明确是 a2
        base = datetime.now()
        m_q1.created_at = base - timedelta(seconds=40)
        m_a1.created_at = base - timedelta(seconds=30)
        m_q2.created_at = base - timedelta(seconds=20)
        m_a2.created_at = base - timedelta(seconds=10)
        db_session.commit()

        assert mgr.delete_last_assistant_message(conv.id) is True

        remaining = [m.content for m in mgr.get_messages(conv.id)]
        assert "a2" not in remaining
        assert "a1" in remaining
        assert remaining.count("a1") == 1

    def test_delete_last_assistant_no_assistant_returns_false(self, db_session):
        mgr = ConversationManager(db_session)
        conv = mgr.create_conversation()
        mgr.add_message(conv.id, role="user", content="only user")
        assert mgr.delete_last_assistant_message(conv.id) is False


class TestCommitErrorRollback:
    def test_commit_failure_raises_database_exception(self, db_session, monkeypatch):
        """模拟 SQLAlchemyError，验证 _commit 正确回滚并转抛 DatabaseException。"""
        mgr = ConversationManager(db_session)

        def _fail_commit():
            raise SQLAlchemyError("commit boom")

        rolled_back = {"called": False}
        original_rollback = db_session.rollback

        def _spy_rollback():
            rolled_back["called"] = True
            original_rollback()

        monkeypatch.setattr(db_session, "commit", _fail_commit)
        monkeypatch.setattr(db_session, "rollback", _spy_rollback)

        with pytest.raises(DatabaseException):
            mgr.create_conversation(title="x")

        assert rolled_back["called"] is True

    def test_get_conversation_sqlalchemy_error_raises(self, db_session, monkeypatch):
        mgr = ConversationManager(db_session)

        def _fail_query(*_args, **_kwargs):
            raise SQLAlchemyError("query boom")

        monkeypatch.setattr(db_session, "query", _fail_query)

        with pytest.raises(DatabaseException):
            mgr.get_conversation("anything")
