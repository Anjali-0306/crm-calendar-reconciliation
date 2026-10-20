from datetime import timezone
from django.test import SimpleTestCase

from meetings.services.normalization import (
    normalize_text,
    normalize_email,
    normalize_datetime,
    normalize_crm_datetime,
)


class NormalizationTests(SimpleTestCase):

    def test_normalize_text(self):
        result = normalize_text("  Portfolio   Review  ")
        self.assertEqual(result, "portfolio review")

    def test_malformed_email(self):
        result = normalize_email("David.Park[at]Example.com")
        self.assertEqual(result, "david.park@example.com")

    def test_missing_datetime(self):
        result = normalize_datetime(None)
        self.assertIsNone(result)

    def test_naive_calendar_datetime(self):
        result = normalize_datetime("2025-03-10T14:00:00")

        self.assertEqual(result.hour, 14)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_malformed_crm_date(self):
        result = normalize_crm_datetime(
            "03-15/2025", "10:30"
        )

        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 10)

    def test_missing_crm_time(self):
        result = normalize_crm_datetime(
            "2025-03-15", None
        )

        self.assertIsNone(result)