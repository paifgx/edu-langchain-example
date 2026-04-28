# Übung 01 — Support Copilot: Fundament

**Freigabezeitpunkt:** nach den Grundlagenblöcken zu LangChain, LCEL, Structured Output und Memory.  
**Behandelte Parts:** Einstieg/Setup, Architektur & LCEL, Structured Output, Batch/Kosten-Grundlagen, Memory.  
**Noch nicht Teil dieser Übung:** Agents, RAG, LangSmith-Evaluation, Security-Härtung, Production-Review.

Ihr baut das Fundament für einen kleinen, produktionsnah gedachten **Support Copilot**. Die späteren Übungsblätter erweitern genau diesen Stand — ihr müsst also nicht alles in dieser Übung lösen.

## Wichtig: keine Copy-Paste-Übung

Ihr bekommt bewusst **keine vollständige Implementierung** und keine Musterlösung zum Abschreiben. Die Aufgaben beschreiben Ziel, Randbedingungen und Akzeptanzkriterien. Architektur, Modulzuschnitt, Prompt-Details, Fehlerbehandlung und konkrete LCEL-Komposition entscheidet ihr selbst.

Erwartung: Ihr seid Python-fit. Nutzt die Slides, die LangChain-Doku und eure Engineering-Erfahrung. Wenn etwas fehlschlägt, debuggt schrittweise: Eingabetyp, Prompt-Rendering, Modelloutput, Parser/Schema, nächster Runnable.

---

## Zielbild am Ende von Übung 01

Eure Anwendung kann eingehende Support-Tickets analysieren und daraus eine erste Antwort vorbereiten:

- Ticket klassifizieren: Kategorie, Priorität, Sentiment, Sprache, Eskalationsbedarf
- strukturierte Ergebnisse als Pydantic-Objekte liefern
- Keywords und Kurzsummary parallel berechnen
- abhängig von Analyse und Priorität eine Antwort oder Eskalationsnotiz erzeugen
- mehrere Beispiel-Tickets per `.batch()` verarbeiten
- Token/Kosten und optional erste LangSmith-Traces sichtbar machen
- Follow-up-Fragen in getrennten Sessions beantworten, ohne History zwischen Nutzern zu vermischen

---

## Projekt-Setup

Legt ein eigenes Arbeitsverzeichnis an. Eine mögliche Struktur ist:

```text
workshop/
  .env
  pyproject.toml              # oder requirements.txt
  support_copilot/
    config.py
    models.py
    chains.py
    memory.py
    demo_foundation.py
  data/
    tickets.jsonl
  reports/
  tests/
```

Ihr dürft anders strukturieren, solange euer Code nachvollziehbar bleibt und ihr Domain-Modelle, Chain-Definitionen und Demo-/CLI-Code trennt.

Minimal benötigte Themen/Pakete:

- LangChain v1.2.x / LangChain Core
- passendes Provider-Paket, z. B. `langchain-openai`
- Pydantic v2
- `python-dotenv`
- optional LangSmith
- optional `pytest`

`.env` sollte mindestens euren Provider-Key und Modellnamen enthalten. LangSmith-Variablen sind optional, aber für Debugging empfohlen.

### Gemeinsame Regeln

- Nutzt LCEL und Runnables statt alter Chain-Klassen.
- Nutzt Pydantic für strukturierte Outputs statt manuellem JSON-Parsing.
- Keine echten Kundendaten, keine echten Secrets im Repo.
- Kein globaler, ungetrennter Chatverlauf.
- Keine Legacy-Patterns als Neubau: `LLMChain`, `ConversationChain`, `SequentialChain`, `initialize_agent`, `AgentExecutor`.

---

## Aufgabe 1 — Modellzugriff und Konfiguration

**Passend zu:** Setup, Modellwahl, Provider-Konfiguration

Erstellt eine zentrale Konfiguration für Modellzugriff und Laufzeitparameter.

### Anforderungen

- Ladet Konfiguration aus `.env`.
- Kapselt Modellinitialisierung an einer Stelle, statt Modellnamen überall im Code zu verteilen.
- Nutzt standardmäßig eine niedrige Temperatur für reproduzierbare Triage-/Extraktionsaufgaben.
- Baut einen Smoke-Test, der einen einzelnen Modellcall ausführt und mindestens Antwortinhalt sowie verfügbare Nutzungsmetadaten ausgibt.
- Wenn LangSmith aktiv ist: setzt sinnvolle Run-Namen, Tags oder Metadaten.

### Akzeptanzkriterien

- Ein einzelnes Kommando startet euren Smoke-Test.
- Der Modellname ist nicht mehrfach hartcodiert.
- Fehlende optionale LangSmith-Konfiguration bricht die lokale Ausführung nicht.

### Bonus

- Definiert zwei Modellprofile: ein günstiges für Triage, ein stärkeres für Antwortgenerierung.
- Dokumentiert kurz, ab wann ihr auf das stärkere Modell routen würdet.

---

## Aufgabe 2 — Domain-Schemas und Testdaten

**Passend zu:** Structured Output, Pydantic, Entscheidungskriterien

Definiert die fachlichen Objekte, mit denen alle späteren Chains arbeiten. Ihr entscheidet Klassennamen und Feldnamen selbst, aber die Modelle sollen eng genug sein, um schlechte Outputs zu erkennen.

### Anforderungen

Legt mindestens diese fachlichen Konzepte an:

1. **Ticket**
   - ID
   - Kundename optional
   - Kanal: E-Mail, Chat oder Portal
   - Originaltext
2. **Ticketanalyse**
   - Kategorie, z. B. Billing, Bug, How-to, Security, Vertrag, Sonstiges
   - Priorität: Low, Normal, High, Critical
   - Sentiment
   - Sprache
   - Eskalationsbedarf
   - Confidence zwischen 0 und 1
   - kurze Begründung
3. **Keywords**
   - 1 bis 5 relevante Begriffe
4. **Antwort-/Eskalationsentwurf**
   - Kundenantwort oder interne Notiz
   - nächste Aktion

Legt mindestens acht Tickets in `data/tickets.jsonl` an. Nutzt eine Mischung aus Beschwerde, Bug, Frage, Rechnung, Security/PII, Vertragskündigung und Prompt-Injection-Versuch.

Beispielfälle:

- verspätete Lieferung eines Reports an einen Vorstand
- CSV-Export schlägt seit Update mit HTTP 500 fehl
- Frage nach API-Rate-Limits
- doppelte Rechnung
- personenbezogene Daten eines anderen Kunden in einer Antwort
- Prompt-Injection: „Ignore previous instructions ..."

### Akzeptanzkriterien

- Alle Testdaten lassen sich validieren.
- Priorität/Kategorie/Sentiment sind keine beliebigen freien Strings.
- `confidence` ist numerisch begrenzt.
- Security/PII-Fälle sind im Datensatz enthalten.

### Bonus

- Ergänzt Validatoren für kurze Begründungen oder Normalisierung leerer Kundennamen.
- Schreibt einen Test, der alle JSONL-Zeilen lädt und validiert.

---

## Aufgabe 3 — Erste Structured-Output-Chain

**Passend zu:** Prompt Templates, Messages, `with_structured_output`

Baut eine Chain, die aus einem Ticket eine strukturierte Ticketanalyse erzeugt.

### Anforderungen

- Nutzt ein Chat-Prompt-Template mit klarer Systemrolle und separater Nutzer-/Ticketnachricht.
- Nutzt `.with_structured_output(...)` mit eurem Analysemodell.
- Kein manuelles JSON-Parsing.
- Testet die Chain isoliert mit mindestens drei Tickets.
- Baut eine technische Fallback-Strategie, die ein valides Analyseobjekt liefert und menschliche Prüfung erzwingt.

### Akzeptanzkriterien

- Die Chain gibt ein echtes Pydantic-Objekt zurück.
- Ein technischer Fehler in der Analyse bricht nicht die komplette Anwendung.
- Security-/PII-Fälle werden nicht als normale Anfrage ohne Eskalation eingestuft.
- Ihr könnt erklären, welche Felder durch Schema und welche durch Prompt beeinflusst werden.

### Bonus

- Macht Prompt und Schema-Taxonomie explizit konsistent.
- Gebt der Chain einen klaren Namen im Trace.

---

## Aufgabe 4 — LCEL-Pipeline mit parallelen Schritten

**Passend zu:** Runnables, LCEL, Parallelität, State-Akkumulation

Erweitert die Analyse zu einer Pipeline, die unabhängige Aufgaben parallel ausführt und danach abhängig vom Analyseergebnis eine Antwort oder Eskalation vorbereitet.

### Ziel-Datenfluss

```text
Ticket
  ├─ Analyse
  ├─ Keywords
  └─ Kurzsummary
        ↓
  Routing: Antwortentwurf oder Eskalationsnotiz
        ↓
  Ergebnisobjekt / Ergebnis-Dict für Reporting
```

### Anforderungen

- Implementiert getrennte Bausteine für Analyse, Keywords, Summary, Antwortentwurf und Eskalationsnotiz.
- Analyse, Keywords und Summary sollen parallel ausführbar sein.
- Antwortentwurf/Eskalation laufen erst danach, weil sie das Analyseergebnis benötigen.
- Nutzt moderne LCEL-Bausteine. Welche genau, entscheidet ihr.
- Definiert eine Routing-Regel, z. B. Eskalation bei hoher/kritischer Priorität oder `needs_human=True`.
- Das finale Ergebnis muss das Originalticket nicht verlieren.

### Akzeptanzkriterien

- Jeder Baustein ist isoliert testbar.
- Eure Pipeline ist nicht ein einziger Mega-Prompt.
- Ihr könnt zeigen, welche Schritte parallel laufen.
- Kritische Fälle erzeugen keine ungeprüfte Kundenantwort.
- Das finale Ergebnis enthält Analyse, Keywords, Summary und nächste Aktion.

### Bonus

- Messt Laufzeit mit und ohne Parallelisierung.
- Nutzt unterschiedliche Modellprofile für Triage und Antwortgenerierung.
- Ergänzt Fallbacks für weitere Teilchains und begründet, wo sie sinnvoll sind.

---

## Aufgabe 5 — Batch-Verarbeitung, Kosten und erste Traces

**Passend zu:** Runnable-Interface, `.batch()`, Kosten, Tracing-Grundlagen

Verarbeitet eure Beispiel-Tickets als kleine Batch-Pipeline und macht Kosten/Laufzeit sichtbar.

### Anforderungen

- Ladet eure JSONL-Tickets.
- Führt dieselbe Pipeline einzeln und per Batch aus.
- Begrenzt Parallelität bewusst.
- Speichert Ergebnisse unter `reports/`.
- Gebt pro Lauf aus:
  - Anzahl Tickets
  - Laufzeit
  - geschätzte Token/Kosten, soweit verfügbar
  - Anzahl eskalierter Tickets
  - auffällige Fehler

### Akzeptanzkriterien

- Batch-Verarbeitung nutzt dieselbe Pipeline wie Einzelverarbeitung.
- Ein fehlerhaftes Ticket verhindert nicht die Analyse aller anderen Tickets.
- Ihr könnt im Trace oder Log erkennen, welche Subchain teuer/langsam ist.

### Bonus

- Aktiviert Caching für wiederholte identische Calls und messt den Unterschied.
- Baut eine kleine CLI mit Parametern für Input-Datei und Batchgröße.

---

## Aufgabe 6 — Session-getrennte Memory für Follow-up-Fragen

**Passend zu:** Memory, `MessagesPlaceholder`, `RunnableWithMessageHistory`, Session-Isolation

Baut einen kleinen Chat-Modus, der sich auf ein analysiertes Ticket beziehen kann und Follow-up-Fragen beantwortet.

### Anforderungen

- Nutzt ein Prompt-Template mit Systemrolle, History-Slot und aktueller Frage.
- Verwendet ein modernes Message-History-Pattern, z. B. `RunnableWithMessageHistory`.
- Implementiert History-Zugriff über `session_id`.
- Testet mindestens zwei Sessions mit unterschiedlichen Tickets.
- Eine Follow-up-Frage in Session B darf keine Details aus Session A enthalten.
- Begrenzung: History darf nicht unendlich wachsen.

### Akzeptanzkriterien

- Ohne `session_id` gibt es keinen gemeinsamen globalen Verlauf.
- Zwei Sessions sind reproduzierbar isoliert.
- Ihr könnt sagen, wodurch ihr die Übungs-Memory in Produktion ersetzen würdet.

### Bonus

- Schreibt einen Test für Session-Isolation.
- Zeigt im Trace, wo History eingefügt wird.
- Ergänzt eine einfache Redaktionsfunktion für E-Mail-Adressen oder Telefonnummern.

---

## Abschluss Übung 01 — stabiler Stand für spätere Blätter

Am Ende solltet ihr lauffähige Bausteine für folgende Bereiche haben:

- Konfiguration und Modellzugriff
- Pydantic-Domainmodelle
- Triage-/Analyse-Chain mit Structured Output
- LCEL-Pipeline mit parallelen Teilaufgaben
- Batch-Ausführung und Reporting
- session-getrennter Chat-/Memory-Prototyp

### Kurzer Selbstcheck

1. Wo wird der Modellname konfiguriert?
2. Welche Datenform erwartet jede Chain als Input?
3. Welche Outputs sind Pydantic-Objekte, welche sind Strings?
4. Wo gibt es Fallbacks?
5. Welche Teile laufen parallel?
6. Wo wird Memory nach Session getrennt?
7. Was würdet ihr vor Produktion sofort ändern?

### Nicht einbauen

- keine alten Chain-Klassen (`LLMChain`, `ConversationChain`, `SequentialChain`)
- kein ungesichertes `eval`
- keine echten Kundendaten oder Secrets im Repo
- keine unbounded globale Chat-History
- keine Annahme, dass ein gutes Demo-Ergebnis bereits Produktionsqualität ist
