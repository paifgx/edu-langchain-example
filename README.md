# Nutzung

## Live-Handout fuer den umgeplanten Nachmittag

`uebung-live-meeting-copilot-von-null.md`

Neues Null-Projekt mit anderem Use-Case: Meeting-Notizen analysieren, Aufgaben extrahieren und eine Follow-up-Mail erzeugen.

## Bestehender Support-Copilot-Stand

`uv run python -m support_copilot.smoke`

`uv run python -m support_copilot.demo_foundation smoke`

`uv run python -m support_copilot.demo_foundation pipeline-one --ticket-id T-1007`

`uv run python -m support_copilot.batch_job --input data/tickets.jsonl --max-concurrency 3`