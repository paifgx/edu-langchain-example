from langchain_core.messages import HumanMessage

from support_copilot.memory import clear_session_store, get_session_history


def test_session_histories_are_isolated() -> None:
    clear_session_store()
    a = get_session_history("session-a")
    b = get_session_history("session-b")
    assert a is not b
    a.add_messages([HumanMessage(content="secret-from-a")])
    assert len(b.messages) == 0
    assert "secret-from-a" in (a.messages[0].content or "")
