from django.core.management import call_command
from django.test import TestCase

from meetings.models import SourceEvent


class IngestionTests(TestCase):

    def test_repeated_ingestion(self):
        call_command("ingest_events", verbosity=0)

        first_count = SourceEvent.objects.count()

        call_command("ingest_events", verbosity=0)

        second_count = SourceEvent.objects.count()

        self.assertEqual(first_count, 42)
        self.assertEqual(second_count, first_count)

    def test_both_sources_preserved(self):
        call_command("ingest_events", verbosity=0)

        self.assertEqual(
            SourceEvent.objects.filter(source="crm").count(),
            20,
        )

        self.assertEqual(
            SourceEvent.objects.filter(source="calendar").count(),
            22,
        )