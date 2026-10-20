from django.core.management import call_command
from django.test import TestCase

from meetings.models import (
    SourceEvent,
    UnifiedMeeting,
    MeetingSource,
)


class ReconciliationIntegrationTests(TestCase):

    def add_event(self, source, external_id, data):
        return SourceEvent.objects.create(
            source=source,
            external_id=external_id,
            raw_data=data,
        )

    def run_reconciliation(self):
        call_command("reconcile_events", verbosity=0)

    def test_same_meeting_is_merged(self):
        self.add_event("crm", "CRM-1", {
            "subject": "Portfolio Review",
            "client_company": "Meridian Capital",
            "relationship_owner": "Sarah Chen",
            "meeting_date": "2025-03-10",
            "meeting_time": "14:00",
            "status": "Confirmed",
        })

        self.add_event("calendar", "CAL-1", {
            "title": "Portfolio Review - Meridian Capital",
            "organizer": "sarah.chen@firma.com",
            "start_time": "2025-03-10T14:10:00",
            "status": "confirmed",
        })

        self.run_reconciliation()

        self.assertEqual(UnifiedMeeting.objects.count(), 1)

        meeting = UnifiedMeeting.objects.first()
        self.assertEqual(meeting.sources.count(), 2)

    def test_crm_only_meeting_preserved(self):
        self.add_event("crm", "CRM-2", {
            "subject": "Client Introduction",
            "client_company": "Lakeshore Partners",
            "meeting_date": "2025-03-14",
            "meeting_time": "15:00",
            "status": "Scheduled",
        })

        self.run_reconciliation()

        self.assertEqual(UnifiedMeeting.objects.count(), 1)
        self.assertEqual(
            UnifiedMeeting.objects.first().sources.count(),
            1,
        )

    def test_calendar_only_meeting_preserved(self):
        self.add_event("calendar", "CAL-2", {
            "title": "Weekly Team Sync",
            "organizer": "sarah.chen@firma.com",
            "start_time": "2025-03-11T09:00:00",
            "status": "confirmed",
        })

        self.run_reconciliation()

        self.assertEqual(UnifiedMeeting.objects.count(), 1)

    def test_duplicate_calendar_records(self):
        event_data = {
            "title": "Team Sync",
            "organizer": "sarah.chen@firma.com",
            "start_time": "2025-03-11T09:00:00",
            "status": "confirmed",
        }

        self.add_event("calendar", "CAL-3", event_data)
        self.add_event("calendar", "CAL-4", event_data.copy())

        self.run_reconciliation()

        self.assertEqual(SourceEvent.objects.count(), 2)
        self.assertEqual(UnifiedMeeting.objects.count(), 1)

        meeting = UnifiedMeeting.objects.first()
        self.assertEqual(meeting.sources.count(), 2)

    def test_cancelled_crm_meeting(self):
        self.add_event("crm", "CRM-5", {
            "subject": "Cancelled Client Meeting",
            "client_company": "Summit Advisors",
            "meeting_date": "2025-03-20",
            "meeting_time": "11:00",
            "status": "Cancelled",
        })

        self.run_reconciliation()

        meeting = UnifiedMeeting.objects.first()

        self.assertIsNotNone(meeting)
        self.assertEqual(meeting.status.lower(), "cancelled")

    def test_repeated_reconciliation(self):
        self.add_event("calendar", "CAL-6", {
            "title": "Client Meeting",
            "start_time": "2025-03-20T12:00:00",
            "status": "confirmed",
        })

        self.run_reconciliation()
        first_count = UnifiedMeeting.objects.count()

        self.run_reconciliation()

        self.assertEqual(
            UnifiedMeeting.objects.count(),
            first_count,
        )