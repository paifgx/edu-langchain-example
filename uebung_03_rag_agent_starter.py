# pyright: reportMissingImports=false
"""
Übung 03 – Starter-Code / Vertiefung
Thema: RAG + Agent-Integration mit Gedächtnis

Aufgabe: Baut einen Agent, der:
1) Über eine Wissensbasis (PDF/Text) per RAG Fragen beantwortet
2) Außerdem einen Taschenrechner-Tool hat
3) Multi-Turn-Gespräche führen kann (InMemorySaver)
4) Optional: Human-in-the-Loop vor teuren Operationen

Zeitbedarf: ca. 60-75 Minuten
"""
import ast
import operator
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  # pyright: ignore[reportMissingImports]

load_dotenv()

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"), temperature=0)

# ── 1) Wissensbasis vorbereiten ─────────────────────────────────
# Beispiel-Texte (in echter Umgebung: PDF/Confluence/Notion)
WISSEN = """
LangChain ist ein Framework für LLM-Anwendungen.
LCEL (LangChain Expression Language) nutzt den Pipe-Operator für Chains.
LangGraph ermöglicht zustandsbasierte Agenten mit Graphen.
LangSmith ist das Observability-Tool für LangChain-Anwendungen.
Vektor-Datenbanken speichern Embeddings für semantische Suche.
RAG steht für Retrieval-Augmented Generation.
"""

# Wissensbasis aufbauen
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
from langchain_core.documents import Document  # pyright: ignore[reportMissingImports]
docs = splitter.split_documents([Document(page_content=WISSEN)])
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


# ── 2) Tools definieren ─────────────────────────────────────────

@tool
def rag_suche(frage: str) -> str:
    """Sucht in der LangChain-Wissensbasis nach relevanten Informationen."""
    docs = retriever.invoke(frage)
    return "\n\n".join(d.page_content for d in docs)


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _safe_eval(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    raise ValueError("Nur Zahlen und +, -, *, /, ** sind erlaubt")


@tool
def taschenrechner(ausdruck: str) -> str:
    """
    Berechnet einen mathematischen Ausdruck.
    Nur einfache Arithmetik: +, -, *, /, ** erlaubt.
    Beispiel: '2 ** 10 + 500'
    """
    try:
        tree = ast.parse(ausdruck, mode="eval")
        return str(_safe_eval(tree.body))
    except Exception as e:
        return f"Fehler: {e}"


tools = [rag_suche, taschenrechner]


# ── 3) TODO: Agent mit create_agent + InMemorySaver ──────────────
# Erstellt:
# - InMemorySaver() als Checkpointer
# - create_agent(llm, tools=tools, checkpointer=memory, system_prompt=...)
# Speichert in: agent

# memory = InMemorySaver()
# agent = create_agent(
#     llm,
#     tools=tools,
#     checkpointer=memory,
#     system_prompt="Nutze Tools für Doku-Suche und Berechnungen. Rate nicht.",
# )


# ── 4) Multi-Turn-Test ──────────────────────────────────────────
# config = {"configurable": {"thread_id": "test-session-1"}}
#
# # Runde 1
# result1 = agent.invoke(
#     {"messages": [HumanMessage(content="Was ist LCEL?")]},
#     config=config
# )
# print("Antwort 1:", result1["messages"][-1].content)
#
# # Runde 2 – Agent soll sich an Runde 1 erinnern
# result2 = agent.invoke(
#     {"messages": [HumanMessage(content="Und wie hängt das mit LangGraph zusammen?")]},
#     config=config
# )
# print("Antwort 2:", result2["messages"][-1].content)
#
# # Runde 3 – Taschenrechner testen
# result3 = agent.invoke(
#     {"messages": [HumanMessage(content="Berechne 2 hoch 10 plus 500")]},
#     config=config
# )
# print("Antwort 3:", result3["messages"][-1].content)
