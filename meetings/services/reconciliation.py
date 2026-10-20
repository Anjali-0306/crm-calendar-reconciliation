from difflib import SequenceMatcher
import re
from meetings.services.normalization import normalize_crm_datetime, normalize_datetime, normalize_text, normalize_email


def similarity(left, right):
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio() if left and right else 0.0


def words(value):
    return set(re.findall(r"[a-z0-9]+", normalize_text(value))) - {"the", "and", "with", "meeting", "session", "call", "review"}


def name_in_email(name, email):
    parts = normalize_text(name).split()
    prefix = normalize_email(email).split("@")[0]
    return len(parts) >= 2 and prefix == f"{parts[0]}.{parts[-1]}"


def calculate_match_score(crm, calendar):
    # Conservative matching: time or date agreement AND contextual evidence are necessary.
    ct = normalize_crm_datetime(crm.get("meeting_date"), crm.get("meeting_time"))
    kt = normalize_datetime(calendar.get("start_time"))
    if ct and kt and ct.date() != kt.date():
        return 0.0
    score = 0.0
    if ct and kt:
        minutes = abs((ct - kt).total_seconds()) / 60
        if minutes <= 15: score += 0.35
        elif minutes <= 60: score += 0.25
        elif minutes <= 120: score += 0.12
        elif minutes <= 360: score += 0.03  # possible timezone mismatch, not sufficient alone
    elif kt and crm.get("meeting_date"):
        # Missing CRM time: date alone is weak evidence.
        from datetime import datetime
        try:
            from meetings.services.normalization import normalize_crm_date
            if normalize_crm_date(crm.get("meeting_date")) == kt.date(): score += 0.12
        except (ValueError, TypeError): pass
    title = calendar.get("title") or ""
    company = normalize_text(crm.get("client_company"))
    if company and company != "none":
        cwords = words(company)
        twords = words(title + " " + (calendar.get("description") or ""))
        if cwords and cwords.issubset(twords): score += 0.30
        elif cwords and len(cwords & twords) >= 1: score += 0.17
    subject = crm.get("subject") or ""
    common = words(subject) & words(title + " " + (calendar.get("description") or ""))
    if common:
        score += min(0.23, 0.10 + 0.065 * len(common))
    else:
        score += 0.10 * similarity(subject, title)
    owner = crm.get("relationship_owner")
    emails = [calendar.get("organizer")] + (calendar.get("attendees") or [])
    if any(name_in_email(owner, e) for e in emails if isinstance(e, str)): score += 0.15
    if crm.get("location") and calendar.get("location") and similarity(crm["location"], calendar["location"]) >= 0.75:
        score += 0.05
    # No automatic match solely on shared organizer/time.
    if not common and not (company and (words(company) & words(title + " " + (calendar.get("description") or "")))):
        return min(round(score, 3), 0.49)
    return round(min(score, 1.0), 3)


def detect_conflicts(crm, calendar):
    result = []
    def add(field, a, b):
        if a is not None and b is not None and normalize_text(a) != normalize_text(b):
            result.append({"field": field, "crm_value": a, "calendar_value": b})
    add("location", crm.get("location"), calendar.get("location"))
    # Completed and confirmed are not equivalent; report rather than resolve silently.
    add("status", crm.get("status"), calendar.get("status"))
    ct = normalize_crm_datetime(crm.get("meeting_date"), crm.get("meeting_time"))
    kt = normalize_datetime(calendar.get("start_time"))
    if ct and kt and abs((ct-kt).total_seconds()) > 15*60:
        result.append({"field": "start_time", "crm_value": ct.isoformat(), "calendar_value": kt.isoformat()})
    meeting_type = normalize_text(crm.get("meeting_type"))
    location = normalize_text(calendar.get("location"))
    if meeting_type in {"in-person", "in person"} and any(x in location for x in ("zoom", "teams", "meet.google", "virtual")):
        result.append({"field": "meeting_mode", "crm_value": crm.get("meeting_type"), "calendar_value": calendar.get("location")})
    return result
