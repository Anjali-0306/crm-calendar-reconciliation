from django.test import SimpleTestCase
from meetings.services.reconciliation import calculate_match_score, detect_conflicts

class ReviewCases(SimpleTestCase):
    def test_unrelated_same_time_same_organizer_not_matched(self):
        crm = {"subject":"Budget Planning", "meeting_date":"2025-03-10", "meeting_time":"10:00", "relationship_owner":"Sarah Chen"}
        cal = {"title":"Customer Onboarding", "start_time":"2025-03-10T10:00:00", "organizer":"sarah.chen@firma.com"}
        self.assertLess(calculate_match_score(crm, cal), .65)

    def test_time_and_mode_conflicts(self):
        crm = {"meeting_date":"2025-03-10", "meeting_time":"10:00", "meeting_type":"In-Person", "location":"Office"}
        cal = {"start_time":"2025-03-10T11:00:00", "location":"Zoom"}
        fields = {c["field"] for c in detect_conflicts(crm, cal)}
        self.assertIn("start_time", fields)
        self.assertIn("meeting_mode", fields)
