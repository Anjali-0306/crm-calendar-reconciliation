import re
from datetime import datetime, timezone

from django.utils.dateparse import parse_datetime


def normalize_text(value):
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower(),
    )


def normalize_email(value):
    if not value:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("[at]", "@")
    )


def normalize_datetime(value):
    if not value:
        return None

    value = str(value).strip()

    parsed = parse_datetime(value)

    if parsed is None:
        return None

    if parsed.tzinfo is None:
        # Explicit assessment assumption:
        # naive timestamps represent UTC.
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def normalize_crm_datetime(date_value, time_value):
    if not date_value:
        return None

    date_value = str(date_value).strip()

    for fmt in ("%Y-%m-%d", "%m-%d/%Y", "%m/%d/%Y"):
        try:
            parsed_date = datetime.strptime(date_value, fmt)
            break
        except ValueError:
            continue
    else:
        return None

    if not time_value:
        return None

    return normalize_datetime(
        f"{parsed_date:%Y-%m-%d}T{time_value}"
    )

def normalize_crm_date(date_value):
    if not date_value:
        return None
    for fmt in ("%Y-%m-%d", "%m-%d/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(date_value).strip(), fmt).date()
        except ValueError:
            pass
    return None
