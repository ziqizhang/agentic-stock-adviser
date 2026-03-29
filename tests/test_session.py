"""Tests for in-memory session store."""

from langchain_core.messages import HumanMessage

from stock_adviser.api.session import SessionStore


class TestSessionStore:
    def test_create_new_session(self):
        store = SessionStore()
        session = store.get_or_create("abc-123")
        assert session == []

    def test_get_existing_session(self):
        store = SessionStore()
        store.get_or_create("abc-123")
        msg = HumanMessage(content="hello")
        store.append("abc-123", msg)
        session = store.get_or_create("abc-123")
        assert len(session) == 1
        assert session[0].content == "hello"

    def test_append_message(self):
        store = SessionStore()
        store.get_or_create("abc-123")
        store.append("abc-123", HumanMessage(content="first"))
        store.append("abc-123", HumanMessage(content="second"))
        session = store.get_or_create("abc-123")
        assert len(session) == 2

    def test_append_to_nonexistent_session_creates_it(self):
        store = SessionStore()
        store.append("new-id", HumanMessage(content="hello"))
        session = store.get_or_create("new-id")
        assert len(session) == 1

    def test_update_replaces_messages(self):
        store = SessionStore()
        store.get_or_create("abc-123")
        new_messages = [HumanMessage(content="updated")]
        store.update("abc-123", new_messages)
        session = store.get_or_create("abc-123")
        assert len(session) == 1
        assert session[0].content == "updated"

    def test_sessions_are_isolated(self):
        store = SessionStore()
        store.append("session-1", HumanMessage(content="one"))
        store.append("session-2", HumanMessage(content="two"))
        assert len(store.get_or_create("session-1")) == 1
        assert len(store.get_or_create("session-2")) == 1
        assert store.get_or_create("session-1")[0].content == "one"
