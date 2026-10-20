import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from meetings.models import SourceEvent


class Command(BaseCommand):
    help = "Import and validate CRM and calendar events"

    @transaction.atomic
    def handle(self, *args, **options):
        sources = [("crm", "crm_events.json", "crm_id"), ("calendar", "calendar_events.json", "event_id")]
        for source, filename, id_field in sources:
            path = settings.BASE_DIR / "data" / filename
            try:
                with path.open(encoding="utf-8") as f:
                    records = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                raise CommandError(f"Cannot load {path}: {exc}") from exc
            if not isinstance(records, list):
                raise CommandError(f"{filename}: expected a JSON list")
            seen = set()
            for index, record in enumerate(records, 1):
                if not isinstance(record, dict) or not isinstance(record.get(id_field), str) or not record[id_field].strip():
                    raise CommandError(f"{filename} record {index}: missing/invalid {id_field}")
                external_id = record[id_field].strip()
                if external_id in seen:
                    raise CommandError(f"{filename}: duplicate ID {external_id}")
                seen.add(external_id)
                SourceEvent.objects.update_or_create(source=source, external_id=external_id, defaults={"raw_data": record})
            # Snapshot semantics: records absent from the supplied file are removed.
            SourceEvent.objects.filter(source=source).exclude(external_id__in=seen).delete()
            self.stdout.write(self.style.SUCCESS(f"Imported {len(records)} {source} events"))
