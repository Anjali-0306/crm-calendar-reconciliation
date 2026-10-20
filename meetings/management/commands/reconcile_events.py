
from django.core.management.base import BaseCommand
from django.db import transaction

from meetings.models import (
    SourceEvent,
    UnifiedMeeting,
    MeetingSource,
)
from meetings.services.reconciliation import (
    calculate_match_score,
    detect_conflicts,
)
from meetings.services.normalization import (
    normalize_datetime,
    normalize_crm_datetime,
)


MATCH_THRESHOLD = 0.65


def calendar_duplicate_key(data):
    """
    Identify exact calendar duplicates.

    Different occurrences of a recurring meeting
    remain separate because their start times differ.
    """
    title = (data.get("title") or "").strip().casefold()
    organizer = (
        data.get("organizer") or ""
    ).strip().casefold()

    start = normalize_datetime(data.get("start_time"))

    if not title or not organizer or start is None:
        return None

    return (title, organizer, start)


def create_source_link(meeting, event):
    """
    Avoid linking the same source event twice
    to the same unified meeting.
    """
    MeetingSource.objects.get_or_create(
        meeting=meeting,
        event=event,
    )


class Command(BaseCommand):
    help = "Reconcile CRM and calendar events"

    @transaction.atomic
    def handle(self, *args, **options):

        # Rebuild unified results without deleting raw events.
        UnifiedMeeting.objects.all().delete()

        crm_events = list(
            SourceEvent.objects.filter(source="crm")
            .order_by("external_id", "pk")
        )

        calendar_events = list(
            SourceEvent.objects.filter(source="calendar")
            .order_by("external_id", "pk")
        )

        # --------------------------------------------------
        # 1. Generate all candidate CRM-calendar matches.
        # --------------------------------------------------
        candidates = []

        for crm_event in crm_events:
            for cal_event in calendar_events:

                score = calculate_match_score(
                    crm_event.raw_data,
                    cal_event.raw_data,
                )

                if score is not None and score >= MATCH_THRESHOLD:
                    candidates.append(
                        (score, crm_event, cal_event)
                    )

        # Maximum-weight one-to-one assignment (small assessment dataset).
        # Dynamic programming over calendar subsets, allowing unmatched CRM events.
        from functools import lru_cache
        calendar_index = {event.pk: i for i, event in enumerate(calendar_events)}
        crm_index = {event.pk: i for i, event in enumerate(crm_events)}
        options = [[] for _ in crm_events]
        for score, crm_event, cal_event in candidates:
            options[crm_index[crm_event.pk]].append((calendar_index[cal_event.pk], score))

        @lru_cache(None)
        def best(i, used):
            if i == len(crm_events):
                return (0.0, ())
            best_score, best_pairs = best(i + 1, used)
            for j, score in options[i]:
                if used & (1 << j):
                    continue
                remaining, pairs = best(i + 1, used | (1 << j))
                total = score + remaining
                if total > best_score + 1e-9:
                    best_score, best_pairs = total, ((i, j, score),) + pairs
            return (best_score, best_pairs)

        _, assignment = best(0, 0)
        matched_pairs = [(crm_events[i], calendar_events[j], score) for i, j, score in assignment]
        matched_crm_ids = {c.pk for c, _, _ in matched_pairs}
        matched_calendar_ids = {c.pk for _, c, _ in matched_pairs}

        created_count = 0
        duplicate_count = 0

        # Maps exact calendar identities to unified meetings.
        calendar_meeting_map = {}

        # --------------------------------------------------
        # 2. Create meetings from matched CRM-calendar pairs.
        # --------------------------------------------------
        for crm_event, cal_event, score in matched_pairs:

            crm = crm_event.raw_data
            calendar = cal_event.raw_data

            crm_start = normalize_crm_datetime(
                crm.get("meeting_date"),
                crm.get("meeting_time"),
            )

            calendar_start = normalize_datetime(
                calendar.get("start_time")
            )

            conflicts = detect_conflicts(crm, calendar)

            title_source = (
                "calendar" if calendar.get("title") else "crm"
            )

            time_source = (
                "calendar" if calendar_start else "crm"
            )

            location_source = (
                "calendar"
                if calendar.get("location")
                else "crm"
            )

            status_source = (
                "crm" if crm.get("status") else "calendar"
            )

            meeting = UnifiedMeeting.objects.create(
                title=(
                    calendar.get("title")
                    or crm.get("subject")
                    or "Untitled Meeting"
                ),
                start_time=calendar_start or crm_start,
                location=(
                    calendar.get("location")
                    or crm.get("location")
                ),
                status=(
                    crm.get("status")
                    or calendar.get("status")
                    or "unknown"
                ),
                conflicts=conflicts,
                provenance={
                    "title": title_source,
                    "start_time": time_source,
                    "location": location_source,
                    "status": status_source,
                },
            )

            create_source_link(meeting, crm_event)
            create_source_link(meeting, cal_event)

            key = calendar_duplicate_key(calendar)

            if key is not None:
                calendar_meeting_map[key] = meeting

            created_count += 1

        # --------------------------------------------------
        # 3. Preserve unmatched CRM records.
        # --------------------------------------------------
        for crm_event in crm_events:

            if crm_event.pk in matched_crm_ids:
                continue

            crm = crm_event.raw_data

            meeting = UnifiedMeeting.objects.create(
                title=(
                    crm.get("subject")
                    or "Untitled Meeting"
                ),
                start_time=normalize_crm_datetime(
                    crm.get("meeting_date"),
                    crm.get("meeting_time"),
                ),
                location=crm.get("location"),
                status=crm.get("status") or "unknown",
                conflicts=[],
                provenance={
                    "title": "crm",
                    "start_time": "crm",
                    "location": "crm",
                    "status": "crm",
                },
            )

            create_source_link(meeting, crm_event)
            created_count += 1

        # --------------------------------------------------
        # 4. Process remaining calendar records.
        # --------------------------------------------------
        for cal_event in calendar_events:

            if cal_event.pk in matched_calendar_ids:
                continue

            calendar = cal_event.raw_data
            key = calendar_duplicate_key(calendar)

            # Exact duplicate of either an existing matched
            # meeting or another calendar-only meeting.
            if (
                key is not None
                and key in calendar_meeting_map
            ):
                existing_meeting = calendar_meeting_map[key]

                create_source_link(
                    existing_meeting,
                    cal_event,
                )

                duplicate_count += 1
                continue

            # Preserve calendar-only events.
            start_time = normalize_datetime(
                calendar.get("start_time")
            )

            meeting = UnifiedMeeting.objects.create(
                title=(
                    calendar.get("title")
                    or "Untitled Meeting"
                ),
                start_time=start_time,
                location=calendar.get("location"),
                status=(
                    calendar.get("status")
                    or "unknown"
                ),
                conflicts=[],
                provenance={
                    "title": "calendar",
                    "start_time": "calendar",
                    "location": "calendar",
                    "status": "calendar",
                },
            )

            create_source_link(meeting, cal_event)

            if key is not None:
                calendar_meeting_map[key] = meeting

            created_count += 1

        # --------------------------------------------------
        # 5. Report reconciliation statistics.
        # --------------------------------------------------
        self.stdout.write(
            self.style.SUCCESS(
                "Reconciliation completed successfully!\n"
                f"Unified meetings created: {created_count}\n"
                f"CRM-calendar pairs matched: {len(matched_pairs)}\n"
                f"Duplicate calendar records merged: {duplicate_count}\n"
                f"CRM source records: {len(crm_events)}\n"
                f"Calendar source records: {len(calendar_events)}"
            )
        )
