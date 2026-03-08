import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Tuple


# support full and short english month names
_month_re = (
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
)
# parse filenames like "AI TEAM MEETING - July 17 (37 mins)"
_filename_re = re.compile(
    rf"^(?P<title>.+?)\s*-\s*(?P<month>{_month_re})\s+(?P<day>\d{{1,2}})\s*(?:\((?P<mins>\d+)\s*mins\))?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedMeeting:
    title: str
    meeting_date: date
    duration_mins: Optional[int]


def _clean_stem(stem: str) -> str:
    # normalize whitespace in the filename stem
    cleaned = re.sub(r"\s+", " ", stem).strip()
    return cleaned

def _parse_month(month: str) -> int:
    # parse either a full month name or a short month name
    normalized = month.strip()

    try:
        return datetime.strptime(normalized, "%B").month
    except ValueError:
        return datetime.strptime(normalized, "%b").month


def _parse_month_day(stem: str) -> Optional[Tuple[str, int, Optional[int], str]]:
    # extract title, month, day, and optional duration from a filename stem
    stem = _clean_stem(stem)

    # strip duration if it is present but not at the end in some variants
    stem = re.sub(r"\s*\(\s*(\d+)\s*mins\s*\)\s*$", r" (\1 mins)", stem, flags=re.IGNORECASE)

    match = _filename_re.match(stem)
    if not match:
        return None

    title = _clean_stem(match.group("title"))
    month = match.group("month")
    day = int(match.group("day"))
    mins = match.group("mins")
    duration = int(mins) if mins else None

    # keep original month token for later parsing
    return title, day, duration, month


def parse_meeting_from_path(file_path: Path) -> ParsedMeeting:
    # parse meeting metadata from filename and file modified time
    stem = file_path.stem
    fallback_date = date.fromtimestamp(file_path.stat().st_mtime)
    fallback_year = fallback_date.year

    parsed = _parse_month_day(stem)
    if not parsed:
        # fall back to file metadata when parsing fails
        return ParsedMeeting(
            title=_clean_stem(stem),
            meeting_date=fallback_date,
            duration_mins=None,
        )

    title, day, duration, month = parsed
    month_index = _parse_month(month)
    meeting_dt = date(fallback_year, month_index, day)

    # adjust year if parsed meeting date falls in the future
    today = date.today()
    if meeting_dt > today:
        meeting_dt = date(fallback_year - 1, month_index, day)

    return ParsedMeeting(
        title=title,
        meeting_date=meeting_dt,
        duration_mins=duration,
    )