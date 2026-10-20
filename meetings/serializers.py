from rest_framework import serializers
from .models import UnifiedMeeting, MeetingSource


class MeetingSourceSerializer(serializers.ModelSerializer):
    source = serializers.CharField(
        source="event.source",
        read_only=True,
    )
    external_id = serializers.CharField(
        source="event.external_id",
        read_only=True,
    )
    raw_data = serializers.JSONField(
        source="event.raw_data",
        read_only=True,
    )

    class Meta:
        model = MeetingSource
        fields = ["source", "external_id", "raw_data"]


class UnifiedMeetingSerializer(serializers.ModelSerializer):
    sources = MeetingSourceSerializer(many=True, read_only=True)

    class Meta:
        model = UnifiedMeeting
        fields = [
            "id",
            "title",
            "start_time",
            "location",
            "status",
            "conflicts",
            "provenance",
            "sources",
        ]