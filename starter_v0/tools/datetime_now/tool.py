from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from tools._shared import err

# Fixed offsets (hours) so the tool works without the tzdata package (Windows).
# Daylight saving is NOT modelled; "america/new_york" etc. use standard time.
ZONE_OFFSETS = {
    "utc": 0, "gmt": 0,
    "asia/ho_chi_minh": 7, "asia/saigon": 7, "vietnam": 7, "vn": 7, "hanoi": 7,
    "asia/bangkok": 7, "asia/singapore": 8, "asia/tokyo": 9, "japan": 9, "asia/seoul": 9,
    "asia/shanghai": 8, "asia/kolkata": 5.5, "europe/london": 0, "europe/paris": 1,
    "europe/berlin": 1, "america/new_york": -5, "america/chicago": -6,
    "america/los_angeles": -8, "australia/sydney": 10,
}
_OFFSET_RE = re.compile(r"^(?:utc|gmt)\s*([+-])\s*(\d{1,2})(?::?(\d{2}))?$", re.IGNORECASE)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve(tz: str) -> tuple[str, timezone]:
    raw = " ".join((tz or "UTC").split()) or "UTC"
    key = raw.lower()
    if key in ZONE_OFFSETS:
        return raw, timezone(timedelta(hours=ZONE_OFFSETS[key]))
    match = _OFFSET_RE.match(key)
    if not match:
        raise ValueError(f"Unknown timezone '{tz}'. Use e.g. 'UTC', 'Asia/Ho_Chi_Minh' or 'UTC+7'.")
    hours_part, minutes_part = int(match.group(2)), int(match.group(3) or 0)
    if hours_part > 14 or minutes_part > 59:
        raise ValueError(f"UTC offset out of range: '{tz}'")
    sign = 1 if match.group(1) == "+" else -1
    offset = timedelta(hours=hours_part, minutes=minutes_part) * sign
    label = f"UTC{match.group(1)}{hours_part}" + (f":{minutes_part:02d}" if minutes_part else "")
    return label, timezone(offset)


def get_datetime_now(timezone_name: str = "UTC") -> dict[str, Any]:
    try:
        label, tzinfo = _resolve(timezone_name)
        now = _utcnow().astimezone(tzinfo)
        return {
            "tool": "datetime_now",
            "timezone": label,
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "utc_offset": now.strftime("%z"),
        }
    except Exception as exc:
        return err("datetime_now", exc)
