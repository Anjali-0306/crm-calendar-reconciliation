from django.db import models


class SourceEvent(models.Model):
    SOURCE_CHOICES = [
        ("crm", "CRM"),
        ("calendar", "Calendar"),
    ]

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
    )
    external_id = models.CharField(max_length=100)
    raw_data = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="unique_source_event",
            )
        ]


class UnifiedMeeting(models.Model):
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField(
        null=True,
        blank=True,
    )
    location = models.TextField(
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=50)
    conflicts = models.JSONField(default=list)
    provenance = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)


class MeetingSource(models.Model):
    meeting = models.ForeignKey(
        UnifiedMeeting,
        on_delete=models.CASCADE,
        related_name="sources",
    )
    event = models.ForeignKey(
        SourceEvent,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "event"],
                name="unique_meeting_source",
            )
        ]