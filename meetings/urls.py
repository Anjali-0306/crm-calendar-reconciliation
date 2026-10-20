from django.urls import path
from .views import MeetingListAPIView, dashboard

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path(
        "api/meetings/",
        MeetingListAPIView.as_view(),
        name="meeting-list",
    ),
]