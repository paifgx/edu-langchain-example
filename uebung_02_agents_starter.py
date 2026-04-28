# pyright: reportMissingImports=false
"""
Übung 02 – Starter-Code
Thema: Agents & Tools ohne RAG

Aufgabe: Baut einen Agent, der:
1) ein Datums-Tool nutzt
2) einen sicheren Taschenrechner nutzt
3) optional eure Ticket-Triage aus Übung 01 als Tool aufruft
4) Multi-Turn-Gespräche per thread_id trennt

Zeitbedarf: ca. 45-60 Minuten
"""
from __future__ import annotations

import ast
import operator
from datetime import date
from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver  # pyright: ignore[reportMissingImports]


@tool
def get_current_date() -> str:
    """Gibt das aktuelle Datum im ISO-Format zurück."""
    return date.today().isoformat()


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return float(_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right)))
    raise ValueError("Nur Zahlen und +, -, *, / sind erlaubt")


@tool
def calculate(expression: str) -> str:
    """Berechnet einfache mathematische Ausdrücke mit +, -, *, /. Kein Python-Code."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_safe_eval(tree.body))
    except Exception as exc:
        return f"Fehler: {exc}"


@tool
def analyze_ticket(text: str) -> str:
    """Analysiert ein Support-Ticket kompakt. Ersetze den Mock durch eure Triage-Pipeline aus Übung 01."""
    # TODO: durch eure Pipeline aus Übung 01 ersetzen.
    if "500" in text or "kritisch" in text.lower():
        return "Kategorie: Bug; Priorität: High; Eskalation: ja; Begründung: Produktionsnaher Fehler."
    return "Kategorie: Sonstiges; Priorität: Normal; Eskalation: nein; Begründung: Keine kritischen Signale."


# TODO: Modell aus eurer zentralen Konfiguration verwenden.
llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0)

# TODO: Agent bauen.
checkpointer = InMemorySaver()
tools = [get_current_date, calculate, analyze_ticket]

agent = create_agent(
    model=llm,
    tools=tools,
    checkpointer=checkpointer,
    system_prompt=(
        "Du bist ein Support-Copilot. Nutze Tools für Datum, Berechnungen "
        "und Ticketanalysen. Rate nicht, wenn ein Tool zuständig ist."
    ),
)


def ask(message: str, thread_id: str = "demo-agent-1") -> str:
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": message}]}, config=config)
    return result["messages"][-1].content


if __name__ == "__main__":
    print(ask("Heute ist welches Datum?"))
    print(ask("Berechne (1024 * 1024) / 60."))
    print(ask("Analysiere dieses Ticket: Seit dem Update schlägt der CSV-Export mit HTTP 500 fehl."))
    print(ask("Was war das Ticket aus meiner vorherigen Frage?"))
