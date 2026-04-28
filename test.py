from operator import add
from typing import Annotated

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class MeetingState(TypedDict, total=False):
    """Der Zustand, den LangGraph von Schritt zu Schritt weitergibt."""

    notes: Annotated[list[str], add]
    question: str
    summary: str
    tasks: list[str]
    answer: str


def extract_tasks(notes: list[str]) -> list[str]:
    """Sehr einfache Aufgaben-Erkennung fuer die Demo."""
    tasks: list[str] = []

    for note in notes:
        if "TODO:" not in note:
            continue

        task = note.split("TODO:", maxsplit=1)[1].strip()
        tasks.append(task)

    return tasks


def analyze_meeting(state: MeetingState) -> MeetingState:
    """Erzeugt aus allen bekannten Notizen eine Zusammenfassung und Aufgaben."""
    notes = state.get("notes", [])
    tasks = extract_tasks(notes)

    if notes:
        summary = f"Ich kenne {len(notes)} Meeting-Notiz(en)."
    else:
        summary = "Ich kenne in diesem Thread noch keine Meeting-Notizen."

    return {
        "summary": summary,
        "tasks": tasks,
    }


def answer_question(state: MeetingState) -> MeetingState:
    """Beantwortet eine Frage nur mit dem aktuell vorhandenen Zustand."""
    question = state.get("question", "")
    tasks = state.get("tasks", [])

    if not question:
        answer = "Keine Frage gestellt."
    elif tasks:
        answer = "Ich finde diese gespeicherten Aufgaben: " + "; ".join(tasks)
    else:
        answer = (
            "Ich habe in diesem Thread keine gespeicherten Aufgaben gefunden. "
            "Ohne gespeicherten Zustand fuer diese thread_id fehlt der fruehere "
            "Meeting-Kontext."
        )

    return {"answer": answer}


def build_graph(checkpointer: InMemorySaver | None = None):
    """Baut denselben Graphen wahlweise mit oder ohne Checkpointer."""
    builder = StateGraph(MeetingState)
    builder.add_node("analyze_meeting", analyze_meeting)
    builder.add_node("answer_question", answer_question)

    builder.add_edge(START, "analyze_meeting")
    builder.add_edge("analyze_meeting", "answer_question")
    builder.add_edge("answer_question", END)

    return builder.compile(checkpointer=checkpointer)


def print_result(title: str, result: MeetingState) -> None:
    """Gibt nur die didaktisch wichtigen Felder aus."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print("Zusammenfassung:", result["summary"])
    print("Aufgaben:", result["tasks"] or "-")
    print("Antwort:", result["answer"])


def run_without_checkpointer() -> None:
    """Zeigt: Zwei invoke-Aufrufe sind ohne Checkpointer voneinander getrennt."""
    graph = build_graph()
    config = {"configurable": {"thread_id": "meeting-123"}}

    first_result = graph.invoke(
        {
            "notes": [
                "Anna: Das Budget ist freigegeben. TODO: Bob sendet die Follow-up-Mail."
            ],
            "question": "",
        },
        config,
    )
    print_result("1) Ohne Checkpointer: erster Aufruf mit Meeting-Notiz", first_result)

    second_result = graph.invoke(
        {
            "notes": [],
            "question": "Wer soll die Follow-up-Mail senden?",
        },
        config,
    )
    print_result(
        "2) Ohne Checkpointer: zweiter Aufruf mit gleicher thread_id", second_result
    )


def run_with_checkpointer_same_thread() -> None:
    """Zeigt: Gleiche thread_id bedeutet gleicher gespeicherter Vorgang."""
    checkpointer = InMemorySaver()
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": "meeting-123"}}

    first_result = graph.invoke(
        {
            "notes": [
                "Anna: Das Budget ist freigegeben. TODO: Bob sendet die Follow-up-Mail."
            ],
            "question": "",
        },
        config,
    )
    print_result("3) Mit Checkpointer: erster Aufruf speichert den Zustand", first_result)

    second_result = graph.invoke(
        {
            "notes": [],
            "question": "Wer soll die Follow-up-Mail senden?",
        },
        config,
    )
    print_result(
        "4) Mit Checkpointer: zweiter Aufruf mit gleicher thread_id", second_result
    )


def run_with_checkpointer_other_thread() -> None:
    """Zeigt: Andere thread_id bedeutet anderer gespeicherter Vorgang."""
    checkpointer = InMemorySaver()
    graph = build_graph(checkpointer)

    meeting_123 = {"configurable": {"thread_id": "meeting-123"}}
    meeting_456 = {"configurable": {"thread_id": "meeting-456"}}

    graph.invoke(
        {
            "notes": [
                "Anna: Das Budget ist freigegeben. TODO: Bob sendet die Follow-up-Mail."
            ],
            "question": "",
        },
        meeting_123,
    )

    other_thread_result = graph.invoke(
        {
            "notes": [],
            "question": "Wer soll die Follow-up-Mail senden?",
        },
        meeting_456,
    )
    print_result(
        "5) Mit Checkpointer, aber anderer thread_id: anderer Vorgang",
        other_thread_result,
    )


def main() -> None:
    #run_without_checkpointer()
    #run_with_checkpointer_same_thread()
    run_with_checkpointer_other_thread()


if __name__ == "__main__":
    main()