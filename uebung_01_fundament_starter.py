# pyright: reportMissingImports=false
"""
Übung 01 – Starter-Code
Thema: Support-Copilot-Fundament mit LCEL und Structured Output

Aufgabe: Baut eine Pipeline, die:
1) Die Stimmung eines Textes erkennt (positiv/negativ/neutral + Score)
2) Keywords extrahiert
3) Eine professionelle E-Mail-Antwort generiert
4) Schritte 1+2 parallel ausführt

Zeitbedarf: ca. 45-60 Minuten
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnableLambda
from pydantic import BaseModel, Field

load_dotenv()

# ── Modell ─────────────────────────────────────────────────────
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"), temperature=0)

# ── Pydantic-Schemas ────────────────────────────────────────────
class Sentiment(BaseModel):
    label: str = Field(description="positiv, negativ oder neutral")
    score: float = Field(description="Konfidenz 0.0–1.0")
    begruendung: str = Field(description="Kurze Begründung")

class Keywords(BaseModel):
    begriffe: list[str] = Field(description="3–5 Schlüsselbegriffe")


# ── TODO 1: Sentiment-Chain ─────────────────────────────────────
# Erstellt eine Chain mit:
# - ChatPromptTemplate (Systemrolle + Human-Message mit {text})
# - llm.with_structured_output(Sentiment)
# - Fehlerbehandlung: .with_fallbacks([fallback_llm.with_structured_output(Sentiment)])
# Speichert in: sentiment_chain

# sentiment_chain = ...


# ── TODO 2: Keywords-Chain ──────────────────────────────────────
# Erstellt eine Chain mit:
# - ChatPromptTemplate
# - llm.with_structured_output(Keywords)
# Speichert in: keywords_chain

# keywords_chain = ...


# ── TODO 3: E-Mail-Chain ────────────────────────────────────────
# Bekommt: original_text (str) + sentiment_label (str)
# Gibt aus: professionelle E-Mail (str)
# Hinweis: RunnablePassthrough.assign() für Input-Mapping

# email_chain = ...


# ── TODO 4: Parallel-Pipeline ───────────────────────────────────
# sentiment_chain und keywords_chain sollen parallel laufen
# Nutzt: RunnableParallel(...)

# parallel_analysis = ...


# ── TODO 5: Komplette Pipeline ──────────────────────────────────
# Kombiniert: parallel_analysis | (extrahiert sentiment.label) | email_chain

# full_pipeline = ...


# ── Test-Eingabe ────────────────────────────────────────────────
test_text = """
Wir haben seit drei Wochen einen kritischen Bug in der Produktionsumgebung.
Das Support-Team antwortet nicht, und unsere Kunden beschweren sich täglich.
Die Situation ist unhaltbar und wir erwägen, den Vertrag zu kündigen.
"""

# Wenn alle TODOs umgesetzt: auskommentieren und testen
# result = full_pipeline.invoke({"text": test_text})
# print(result)
