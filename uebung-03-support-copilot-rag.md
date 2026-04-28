# Übung 03 — Support Copilot: RAG & Retrieval

**Freigabezeitpunkt:** nach dem RAG-/Retrieval-Block.  
**Behandelte Parts:** RAG-Architektur, Dokumentqualität, Chunking, Embeddings, Vector Store, Retriever, Retrieval-Evaluation, RAG-Answer-Chain, Quellenpflicht.  
**Noch nicht Teil dieser Übung:** vollständige LangSmith-Evaluation, Security-Red-Team, Kosten-/Skalierungsoptimierung, Production-Review.

Ihr erweitert den Support Copilot um eine kleine Wissensbasis. Ziel ist nicht „Chatbot klingt gut", sondern: Retrieval nachvollziehen, Quellen erhalten und Nichtwissen sauber behandeln.

---

## Zielbild am Ende von Übung 03

Eure Anwendung kann:

- interne Markdown-Dokumente laden und indexieren
- passende Dokument-Chunks per Retriever finden
- Retrieved Documents mit Quellen sichtbar machen
- eine RAG-Answer-Chain bauen, die nur auf Basis des Kontextes antwortet
- nicht beantwortbare Fragen sauber verweigern
- optional die Doku-Suche als Tool in euren Agenten aus Übung 02 integrieren

---

## Voraussetzungen

Ihr braucht aus den vorherigen Übungen:

- Modell- und Embedding-Konfiguration
- Projektstruktur mit `data/` und `reports/`
- optional: Agent aus Übung 02 für die spätere Tool-Integration

### Gemeinsame Regeln

- Indexing und Querying sauber trennen.
- Quellen/Metadaten dürfen beim Splitten und Formatieren nicht verloren gehen.
- RAG-Antworten müssen Quellen nennen oder Nichtwissen sauber markieren.
- Keine echten internen Dokumente oder Kundendaten verwenden.
- Prompt-Injection in Dokumenten ist untrusted Content, keine Systemanweisung.

---

## Aufgabe 1 — Wissensbasis als Markdown-Dokumente anlegen

**Passend zu:** RAG-Architektur, Dokumentqualität, Metadaten

Legt eine kleine interne Wissensbasis an. Nutzt eigene Inhalte, wenn vorhanden. Falls nicht, erstellt Markdown-Dokumente aus den folgenden Fakten. Struktur, Überschriften, Metadaten und Formulierungen wählt ihr selbst.

### Mindestinhalte

**Produkt**

- Produktname: Acme Support Analytics
- Zweck: Analyse und Priorisierung von Support-Tickets
- Zielgruppe: B2B-Supportteams
- Standardantworten sind Entwürfe und müssen bei kritischen Fällen geprüft werden

**Rate-Limits**

- Free: 60 Requests pro Minute
- Pro: 600 Requests pro Minute
- Enterprise: kundenspezifische Limits nach Vertrag
- Batch-Import: maximal 10.000 Tickets pro Stunde
- Bei HTTP 429: exponential backoff, nicht sofort aggressiv retryen

**SLA**

- Critical: Reaktion innerhalb von 1 Stunde
- High: Reaktion innerhalb von 4 Stunden
- Normal: Reaktion bis zum nächsten Arbeitstag
- Billing-Fragen: Reaktion innerhalb von 2 Arbeitstagen
- Security/PII-Vorfälle werden immer eskaliert

**Security**

- Keine rohen personenbezogenen Daten in Prompts, Logs oder Traces speichern
- Tools arbeiten nach Least Privilege
- Schreibende Aktionen benötigen Freigabe
- Audit-Logs werden 180 Tage aufbewahrt
- Prompt-Injection aus Tickets oder Dokumenten ist untrusted Input

**Refunds**

- Rückerstattung kann innerhalb von 14 Tagen nach Rechnungsstellung geprüft werden
- Doppelte Rechnungen werden durch Billing manuell validiert
- SLA-Verstöße führen nicht automatisch zu Rückerstattung, sondern zu Eskalation

**Release Notes**

- Version 2.3 wurde am 2026-03-15 veröffentlicht
- Bekannter Fehler in 2.3.0: CSV-Export kann bei großen Dateien HTTP 500 liefern
- Workaround: JSON-Export verwenden oder CSV-Export auf maximal 50.000 Zeilen begrenzen
- Fix geplant in Version 2.3.1

### Akzeptanzkriterien

- Mindestens fünf Markdown-Dateien liegen unter `data/docs/` oder einem vergleichbaren Pfad.
- Die Dokumente haben klare Überschriften und Quellen-/Metadaten, die Retrieval-Ausgaben nachvollziehbar machen.
- Die Fakten reichen aus, um die späteren Testfragen eindeutig zu beantworten.

### Bonus

- Nutzt YAML-Frontmatter mit `title`, `owner`, `version`, `last_updated`.
- Fügt einen markierten Negativtest ein: ein Dokumentabschnitt mit Prompt-Injection-Anweisung. Dieser Inhalt darf später nicht als Systemanweisung befolgt werden.

---

## Aufgabe 2 — Indexing und Retriever bauen

**Passend zu:** Chunking, Embeddings, Vector Stores, Retriever-Tuning

Implementiert eine lokale RAG-Grundlage für eure Markdown-Dokumente. Ihr entscheidet selbst, welche Funktionen/Klassen ihr dafür baut.

### Anforderungen

- Dokumente laden
- Dokumente splitten
- Embeddings erzeugen
- lokalen Vector Store aufbauen oder laden
- Retriever konfigurieren
- Retrieved Documents mit Quellen lesbar formatieren
- Indexing und Querying sauber trennen; Indexing darf nicht bei jeder Frage unnötig neu laufen

### Designentscheidungen, die ihr treffen sollt

- Chunkgröße und Overlap
- Embedding-Modell
- Vector Store: FAISS, Chroma oder Alternative
- Retriever-Variante und `k`
- Metadatenformat in der späteren Antwort

### Testqueries

- „Welche Rate-Limits gelten im Pro-Plan?"
- „Wie schnell müssen Critical Tickets beantwortet werden?"
- „Was ist der Workaround für den CSV-Export-Fehler?"
- „Was sagt die Doku zu personenbezogenen Daten in Logs?"
- „Welche Rückerstattung gibt es bei SLA-Verstoß?"

### Akzeptanzkriterien

- Der Retriever liefert nachvollziehbare Chunks mit Source-Metadaten.
- Für jede Testquery ist mindestens ein erwartetes Dokument unter den Top-k-Ergebnissen.
- Quellen gehen beim Formatieren nicht verloren.
- Ihr könnt eure Chunking- und Retriever-Entscheidung begründen.

### Bonus

- Vergleicht Similarity, Score-Threshold und MMR.
- Haltet in `reports/rag_eval.md` fest, welche Einstellung für eure Testfragen am besten war.
- Testet lokale Embeddings und dokumentiert Qualitäts-/Kostenunterschiede.

---

## Aufgabe 3 — Kleines Retrieval-Eval-Set

**Passend zu:** Retrieval-Qualität messen, Hit-Rate@k, Debugging

Bevor ihr eine finale Antwort generiert, prüft, ob der Retriever die richtigen Dokumente findet.

### Anforderungen

Erstellt mindestens acht Fragen:

- fünf beantwortbare Fragen mit erwarteter Quelle
- zwei Fragen, die mehrere Dokumente brauchen
- eine nicht beantwortbare Frage

Beispiele:

| Frage                                                      | Erwartete Quelle           |
| ---------------------------------------------------------- | -------------------------- |
| Welche Rate-Limits gelten für Free und Pro?                | Rate-Limit-Doku            |
| Wie wird ein Security/PII-Vorfall behandelt?               | Security + SLA             |
| Wann wurde Version 2.3 veröffentlicht?                     | Release Notes              |
| Was ist der Workaround für CSV-Export HTTP 500?            | Release Notes              |
| Bekommt ein Kunde bei SLA-Verstoß automatisch Geld zurück? | Refunds                    |
| Welche Kubernetes-Version nutzt das Produkt?               | keine Quelle / Nichtwissen |

### Akzeptanzkriterien

- Ihr könnt für jede Frage die Top-k-Chunks ausgeben.
- Ihr unterscheidet Retrieval-Fehler von Antwort-/Prompt-Fehlern.
- Mindestens eine nicht beantwortbare Frage ist enthalten.

### Bonus

- Berechnet eine einfache Hit-Rate@k.
- Speichert Ergebnisse in `reports/rag_eval.md`.

---

## Aufgabe 4 — RAG-Answer-Chain mit Quellen und Nichtwissen

**Passend zu:** LCEL-RAG, Prompting, Quellenpflicht

Baut eine deterministische RAG-Chain, bevor ihr sie in den Agent integriert. Ein Agent ist schwer zu debuggen, wenn der Retriever selbst unklar ist.

### Anforderungen

- Die Chain erhält eine Frage.
- Sie retrievt passende Dokumente.
- Sie formatiert Kontext mit Quellen.
- Sie antwortet nur auf Basis des bereitgestellten Kontextes.
- Sie nennt Quellen.
- Bei fehlendem Kontext verweigert sie sauber, statt aus Modellwissen zu raten.
- Die Umsetzung nutzt erkennbare LCEL-Bausteine und bleibt testbar.

### Akzeptanzkriterien

- Die RAG-Chain beantwortet nicht einfach aus Modellwissen.
- Quellen sind in der finalen Antwort sichtbar.
- Mindestens die nicht beantwortbare Frage wird sauber verweigert.
- Retrieval-Fehler werden als Retrieval-Fehler erkannt, nicht durch Prompt-Raten kaschiert.

### Bonus

- Gebt neben der finalen Antwort auch die verwendeten Chunks aus.
- Ergänzt einen einfachen deterministischen Check: „Antwort enthält mindestens eine Source-ID".

---

## Aufgabe 5 — Optional: RAG als Agent-Tool integrieren

**Passend zu:** RAG + Agent kombiniert, Tool Calling

Wenn ihr Übung 02 abgeschlossen habt, erweitert euren Agenten um ein Tool für die Doku-Suche.

### Anforderungen

- Tool-Name und Beschreibung sollen dem Modell klar sagen, wann die Doku-Suche zu nutzen ist.
- Das Tool gibt kompakte Passagen mit Quellen zurück.
- Der Agent-Systemprompt unterscheidet klar:
  - Doku-/Policy-Fragen → Doku-Suche
  - Berechnungen → Calculator
  - Datum → Date-Tool
  - Ticketanalyse → Triage-Tool
- Wenn keine Quelle vorhanden ist, soll der Agent nicht raten.
- Testet Multi-Tool-Fragen und Follow-ups mit gleicher `thread_id`.

### Testfragen

- „Was ist der Workaround für den CSV-Export-Bug, und welche Priorität hätte ein Ticket dazu?"
- „Wie viele Tage sind seit dem Release von Version 2.3 vergangen?"
- „Ein Kunde meldet doppelte Rechnung und droht mit Kündigung. Welche SLA oder Regel greift?"
- „Und was wäre die nächste Aktion?"  
  Erwartung: nutzt vorherigen Gesprächskontext.

### Akzeptanzkriterien

- Die Tool-Reihenfolge ist im Trace, Stream oder Log nachvollziehbar.
- Der Agent nutzt Doku-Suche für Doku-Fragen und Calculator für Rechenfragen.
- Der Agent kann eine Follow-up-Frage mit derselben `thread_id` beantworten.
- Ohne passende Dokumentenquelle halluziniert der Agent keine Policy.

### Bonus

- Kürzt lange Tool-Ausgaben, ohne Quellen zu verlieren.
- Testet ein Advanced-RAG-Pattern gezielt nur mit Hypothese, z. B. MMR bei zu ähnlichen Chunks.

---

## Abschluss Übung 03 — stabiler RAG-Stand

Am Ende solltet ihr haben:

- Markdown-Wissensbasis
- Indexing-Funktion oder Indexing-Skript
- ladbaren lokalen Vector Store oder klaren Rebuild-Prozess
- Retriever mit erklärter Konfiguration
- kleines Retrieval-Eval-Set
- RAG-Answer-Chain mit Quellen und Nichtwissen
- optional: Doku-Suche als Agent-Tool

### Selbstcheck

1. Welche Dokumente landen im Index?
2. Welche Metadaten bleiben erhalten?
3. Welche Chunks werden für eine konkrete Frage gefunden?
4. Welche Frage kann euer RAG-System nicht beantworten?
5. Woran erkennt ihr, ob ein Fehler im Retrieval oder im Prompt liegt?
6. Welche Einstellung würdet ihr als Erstes ändern: Chunkgröße, `k`, Embedding-Modell, Prompt — und warum?

### Nicht einbauen

- keine unkontrollierte Antwort ohne Quellen
- kein Indexing bei jeder User-Frage
- keine echten Unternehmensdokumente
- keine Annahme, dass RAG Halluzinationen automatisch verhindert
- keine Advanced Patterns ohne Messhypothese
