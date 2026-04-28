# Übung 02 — Support Copilot: Agents & Tools

**Freigabezeitpunkt:** nach dem Agents-/LangGraph-Block.  
**Behandelte Parts:** ReAct, Tool Calling, `create_agent`, Checkpointer, `thread_id`, einfache LangGraph-/Workflow-Entscheidungen, Agent-Debugging.  
**Noch nicht Teil dieser Übung:** RAG-Dokumentensuche, LangSmith-Evaluation, Security-Härtung, Kostenoptimierung, Production-Review.

Ihr erweitert den Stand aus **Übung 01** um einen kleinen Agenten mit ungefährlichen Tools. Ziel ist, Agent-/Tool-/Memory-Probleme isoliert zu verstehen, bevor später Retrieval und Security dazukommen.

---

## Zielbild am Ende von Übung 02

Eure Anwendung kann:

- einen `create_agent`-basierten Agent starten
- einfache Tools per Tool Calling nutzen
- ein Ticket über eure vorhandene Triage-Pipeline analysieren
- Multi-Turn-Fragen mit `thread_id` sauber trennen
- Tool-Schritte per Stream, Log oder Trace sichtbar machen
- erklären, wann `create_agent` reicht und wann ein eigener `StateGraph` sinnvoll wäre

---

## Voraussetzungen

Ihr braucht aus Übung 01 mindestens:

- zentrale Modellkonfiguration
- Ticket-/Analyse-Schemas
- eine lauffähige Triage-/Analyse-Chain oder Pipeline
- Testtickets

Falls euer Stand aus Übung 01 noch nicht vollständig ist: Baut für diese Übung ein kleines Mock-Triage-Tool, das ein kompaktes Analyseobjekt zurückgibt. Der Agent-Teil soll nicht an der perfekten Triage scheitern.

### Gemeinsame Regeln

- Für neue Agents: `langchain.agents.create_agent`, nicht `initialize_agent` oder `AgentExecutor`.
- Tools sind Backend-Funktionen mit Berechtigungen, keine Prompt-Erweiterungen.
- Tool-Ausgaben bleiben kompakt und nachvollziehbar.
- Aufrufe mit Memory immer mit expliziter `thread_id`.
- Keine schreibenden Tools in dieser Übung.

---

## Aufgabe 1 — Ungefährliche Tools definieren

**Passend zu:** Tool Calling, Tool-Schemas, Tool-Output-Design

Erstellt mindestens diese Tools:

1. **`get_current_date()`**
   - liefert aktuelles Datum im ISO-Format
2. **`calculate(expression)`**
   - berechnet einfache mathematische Ausdrücke sicher
   - AST-basierte Auswertung oder vergleichbar sichere Lösung
   - **kein** Python-`eval`
3. **`analyze_ticket(text)`**
   - ruft eure Triage-/Analyse-Pipeline aus Übung 01 auf
   - gibt eine kompakte Zusammenfassung zurück: Kategorie, Priorität, Eskalation, Begründung

### Anforderungen

- Tool-Namen und Docstrings erklären klar, wann das Tool genutzt werden soll.
- Tool-Argumente sind eng typisiert oder per Pydantic beschrieben.
- Fehler werden modellverständlich zurückgegeben, z. B. „Fehler: Ausdruck enthält nicht erlaubte Operation".
- Tool-Outputs sind kurz genug, um sie sinnvoll an das Modell zurückzugeben.

### Testfragen

- „Heute ist welches Datum?"
- „Berechne (1024 \* 1024) / 60."
- „Analysiere dieses Ticket: Seit dem Update schlägt der CSV-Export mit HTTP 500 fehl."

### Akzeptanzkriterien

- Jedes Tool lässt sich isoliert testen.
- Der Calculator führt keine beliebigen Python-Ausdrücke aus.
- Das Ticketanalyse-Tool nutzt eure Pipeline oder einen klar markierten Mock.
- Fehlerfälle führen nicht zu einem unkontrollierten Crash.

---

## Aufgabe 2 — Agent-Shell mit `create_agent`

**Passend zu:** `create_agent`, ReAct-Loop, Checkpointing

Baut einen Agenten, der eure Tools nutzt.

### Anforderungen

- Agent mit `create_agent` erstellen.
- Modell aus eurer zentralen Konfiguration verwenden.
- `InMemorySaver` als Übungs-Checkpointer nutzen.
- Systemprompt kurz halten:
  - Tools nutzen, wenn Datum, Berechnung oder Ticketanalyse nötig sind.
  - Nicht raten, wenn ein Tool zuständig ist.
  - Antwort knapp und nachvollziehbar formulieren.
- Alle Aufrufe mit expliziter `thread_id` ausführen.

### Testfragen

- „Heute ist welches Datum?"
- „Berechne (1024 \* 1024) / 60."
- „Analysiere dieses Ticket: Seit dem Update schlägt der CSV-Export mit HTTP 500 fehl."
- „Was war das Ticket aus meiner vorherigen Frage?"  
  Erwartung: nur mit derselben `thread_id` beantwortbar.

### Akzeptanzkriterien

- Mindestens ein Tool-Call ist im Stream, Log oder Trace sichtbar.
- Memory funktioniert pro `thread_id`; zwei unterschiedliche Threads vermischen sich nicht.
- Der Agent nutzt ein Tool, statt die Berechnung frei zu halluzinieren.
- Ihr könnt erklären, warum `InMemorySaver` nur für Übung/Dev akzeptabel ist.

---

## Aufgabe 3 — Limits und Debugging sichtbar machen

**Passend zu:** Agent-Debugging, Streaming, Limits

Macht nachvollziehbar, was der Agent tut.

### Anforderungen

- Nutzt Streaming-Updates oder eigenes Logging, um Tool-Schritte sichtbar zu machen.
- Setzt mindestens ein sinnvolles Limit:
  - `recursion_limit` im Run-Config oder
  - `ModelCallLimitMiddleware` / `ToolCallLimitMiddleware`, wenn ihr die Middleware nutzt.
- Protokolliert bei einem Testlauf:
  - User-Frage
  - aufgerufene Tools
  - finale Antwort
  - Thread-ID

### Akzeptanzkriterien

- Ihr könnt zeigen, ob der Agent ein Tool aufgerufen hat oder nicht.
- Ein Loop oder zu viele Tool-Calls würden begrenzt.
- Ihr könnt einen konkreten Debugging-Ablauf erklären: Messages → ToolCalls → ToolMessages → finale Antwort.

### Bonus

- Nutzt LangSmith-Tracing bereits in Dev.
- Fügt Tags/Metadaten wie `exercise=02-agents` und `thread_id` hinzu.

---

## Aufgabe 4 — Architekturentscheidung: Standard-Agent oder eigener Graph?

**Passend zu:** `create_agent` vs. eigener LangGraph, State, Conditional Edges

Diese Aufgabe ist bewusst kurz und kann als Design-Notiz statt Code erledigt werden.

### Anforderungen

Erstellt in `reports/agent_architecture.md` eine kurze Entscheidung:

1. Warum reicht für euren aktuellen Stand `create_agent`?
2. Welche zusätzlichen Anforderungen würden für einen eigenen `StateGraph` sprechen?
3. Welche State-Felder würdet ihr dann explizit modellieren?

Beispiele für mögliche eigene State-Felder:

- `ticket_analysis`
- `risk_score`
- `approval_required`
- `tool_errors`
- `final_action`

### Akzeptanzkriterien

- Ihr versteckt Business-State nicht nur als Text im Chatverlauf.
- Ihr könnt mindestens zwei harte Routing-Regeln nennen, die für einen eigenen Graph sprechen würden.
- Ihr könnt erklären: Standard-Agent ist nicht unprofessionell; eigener Graph ist nur sinnvoll, wenn die zusätzliche Kontrolle gebraucht wird.

### Bonus

Baut einen Mini-`StateGraph`, der deterministisch routet:

```text
classify_ticket → if critical/security: escalation_note
                → else: draft_reply
```

Das ist kein Ersatz für den Agenten, sondern ein Vergleich: deterministischer Workflow vs. agentischer Tool-Loop.

---

## Abschluss Übung 02 — stabiler Stand für RAG

Am Ende solltet ihr haben:

- geprüfte Tools
- Agent mit `create_agent`
- Checkpointer und `thread_id`-Nutzung
- sichtbare Tool-Calls
- kurze Architekturentscheidung zu Agent vs. Graph

### Selbstcheck

1. Welche Tool-Beschreibung sieht das Modell?
2. Welche Tool-Outputs gehen zurück ins Modell?
3. Wo verhindert ihr unsichere Berechnungen?
4. Wie trennt ihr zwei Nutzer/Threads?
5. Wo würdet ihr einen Human-in-the-Loop brauchen?
6. Welche Anforderung würde euren Agenten zu einem eigenen LangGraph machen?

### Nicht einbauen

- keine Doku-Suche/RAG — das kommt in Übung 03
- keine schreibenden Produktivaktionen
- kein ungesichertes `eval`
- keine globale Memory ohne `thread_id`
- kein eigener Graph nur aus Prestigegründen
