from django.test import TestCase
from rest_framework.test import APIClient

from meetings.models import UnifiedMeeting


class MeetingAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        UnifiedMeeting.objects.create(
            title="Portfolio Review",
            status="confirmed",
            location="Zoom",
            conflicts=[
                {
                    "field": "location",
                    "crm_value": "In-Person",
                    "calendar_value": "Zoom",
                }
            ],
            provenance={"location": "calendar"},
        )

    def test_api_returns_meetings(self):
        response = self.client.get("/api/meetings/")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        meetings = data if isinstance(data, list) else data["results"]

        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0]["title"], "Portfolio Review")

    def test_api_exposes_conflicts(self):
        response = self.client.get("/api/meetings/")

        data = response.json()
        meetings = data if isinstance(data, list) else data["results"]

        self.assertEqual(
            meetings[0]["conflicts"][0]["field"],
            "location",
        )
        self.assertEqual(
            meetings[0]["provenance"]["location"],
            "calendar",
        )