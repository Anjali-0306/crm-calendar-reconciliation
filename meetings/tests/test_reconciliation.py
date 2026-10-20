from django.test import SimpleTestCase

from meetings.services.reconciliation import (
    calculate_match_score,
    detect_conflicts,

)


class MatchingTests(SimpleTestCase):

    def setUp(self):
        self.crm = {
            "crm_id": "CRM-1001",
            "subject": "Q1 Portfolio Review",
            "client_company": "Meridian Capital",
            "relationship_owner": "Sarah Chen",
            "meeting_date": "2025-03-10",
            "meeting_time": "14:00",
            "location": "Conference Room B",
            "status": "Confirmed",
        }

        self.calendar = {
            "event_id": "CAL-A1",
            "title": "Q1 Portfolio Review - Meridian Capital",
            "organizer": "sarah.chen@firma.com",
            "start_time": "2025-03-10T14:00:00",
            "location": "Conference Room B",
            "status": "confirmed",
        }

    def test_same_meeting_has_high_score(self):
        score = calculate_match_score(
            self.crm, self.calendar
        )

        self.assertGreaterEqual(score, 0.75)

    def test_slightly_different_times(self):
        self.calendar["start_time"] = (
            "2025-03-10T14:10:00"
        )

        score = calculate_match_score(
            self.crm, self.calendar
        )

        self.assertGreaterEqual(score, 0.75)

    def test_conflicting_locations(self):
        self.calendar["location"] = "Zoom"

        conflicts = detect_conflicts(
            self.crm, self.calendar
        )

        self.assertTrue(
            any(
                conflict["field"] == "location"
                for conflict in conflicts
            )
        )

    def test_matching_locations_no_conflict(self):
        conflicts = detect_conflicts(
            self.crm, self.calendar
        )

        self.assertFalse(
            any(
                conflict["field"] == "location"
                for conflict in conflicts
            )
        )

    def test_missing_time_does_not_crash(self):
        self.crm["meeting_time"] = None

        score = calculate_match_score(
            self.crm, self.calendar
        )

        self.assertIsInstance(score, float)