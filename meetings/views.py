from django.shortcuts import render
from rest_framework import generics

from .models import UnifiedMeeting
from .serializers import UnifiedMeetingSerializer


class MeetingListAPIView(generics.ListAPIView):
    serializer_class = UnifiedMeetingSerializer

    def get_queryset(self):
        return (
            UnifiedMeeting.objects
            .prefetch_related("sources__event")
            .order_by("start_time", "id")
        )


def dashboard(request):
    return render(request, "dashboard.html")