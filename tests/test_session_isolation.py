"""History-Store: keine Kreuz-Kontamination zwischen session_ids."""

from langchain_core.messages import AIMessage, HumanMessage

from support_copilot.follow_up import BoundedChatMessageHistory, SessionHistoryStore


def test_bounded_history_truncates() -> None:
    h = BoundedChatMessageHistory(max_messages=4)
    for i in range(10):
        h.add_messages(
            [HumanMessage(content=f"u{i}"), AIMessage(content=f"a{i}")])
    assert len(h.messages) == 4
    assert "u9" in h.messages[-2].content  # type: ignore[union-attr]


def test_session_isolation_in_store() -> None:
    store = SessionHistoryStore()
    sa, sb = store.get("alpha"), store.get("beta")
    sa.add_messages([HumanMessage(content="secret-alpha")])
    sb.add_messages([HumanMessage(content="secret-beta")])
    assert "secret-alpha" not in [m.content for m in sb.messages]
    assert "secret-beta" not in [m.content for m in sa.messages]
