# Event Sync Service (Django + DRF)

Reconciles CRM and calendar records into a unified meeting list, preserving original source records and showing discrepancies.

## Setup (Windows / macOS / Linux)

Python 3.11+ recommended. From the project directory:

```bash
python -m venv .venv
```

Activate it (Windows Command Prompt: `.venv\\Scripts\\activate`; PowerShell: `.venv\\Scripts\\Activate.ps1`; macOS/Linux: `source .venv/bin/activate`), then:

```bash
pip install -r requirements.txt
python start.py
```

Open http://127.0.0.1:8000/ for the dashboard and http://127.0.0.1:8000/api/meetings/ for JSON. After dependencies are installed, `python start.py` is the single startup command. It migrates, ingests, reconciles, then starts the development server.

## Design decisions

- SQLite for easy local execution; Django ORM for persistence, DRF for read-only API.
- SourceEvent stores unmodified input JSON. MeetingSource links source records to unified meetings.
- Matching scores use same-day time proximity, client name, subject/title/description overlap, and organizer/attendees. A conservative threshold of 0.65 avoids merging unrelated records.
- One-to-one CRM/calendar matching maximizes total score globally; records below threshold remain separate.
- Exact calendar duplicates (same title, organizer and start) are linked to the same unified meeting. Near-duplicates are **not automatically merged**, to avoid false positives.
- Calendar values win for title, time and location; CRM status wins when present. `provenance` records this selection. Original values remain available in source data.
- Conflicts are shown for location, status, material time shifts (>15 minutes) and obvious in-person vs video-call differences. Not every difference means an error.
- Timezone assumption: timestamps without an explicit timezone are interpreted as UTC. A five-hour offset is **not automatically corrected** because the source's timezone is unspecified. This may leave some true matches unmatched.
- Reconciliation is an atomic full rebuild; unified IDs are not stable between runs. This is a small assessment simplification, not a production synchronization strategy.
- Ingestion treats each JSON file as a complete source snapshot and removes source records absent from subsequent imports.

## Commands and tests

```bash
python manage.py ingest_events
python manage.py reconcile_events
python manage.py test meetings
```

## Limitations and improvements

Matching is heuristic and should be evaluated with domain-labeled pairs before production. Ambiguous pairs and near-duplicates may require human review. Production should add stable meeting identifiers, incremental sync, configurable source timezones, logging, observability, pagination, and access controls.

## AI assistance transparency

AI assistance were used as a supporting resource during development, primarily for reviewing implementation approaches, exploring reconciliation edge cases, and improving documentation. The final implementation decisions, validation, and testing were handled by the submitter. Matching decisions are heuristic rather than verified business truth.

## Time spent

Approximately 12 hours, including requirement analysis, implementation, testing, debugging, and documentation.
