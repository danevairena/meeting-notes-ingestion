import logging

from .extract_notes import generate_notes_for_meeting
from ..supabase_client import get_supabase_client


# load all meeting ids
def _get_all_meetings() -> list[dict]:
    supabase = get_supabase_client()

    result = (
        supabase.table("meetings")
        .select("id,title")
        .order("created_at", desc=False)
        .execute()
    )

    return result.data or []


# load meeting ids that already have notes
def _get_processed_meeting_ids() -> set[str]:
    supabase = get_supabase_client()

    result = (
        supabase.table("notes")
        .select("meeting_id")
        .execute()
    )

    rows = result.data or []
    return {
        row["meeting_id"]
        for row in rows
        if row.get("meeting_id")
    }


# process all meetings that do not yet have notes
def process_all_meetings_without_notes() -> int:
    meetings = _get_all_meetings()
    processed_meeting_ids = _get_processed_meeting_ids()

    meetings_to_process = [
        meeting
        for meeting in meetings
        if meeting["id"] not in processed_meeting_ids
    ]

    logging.info("found %s meetings without notes", len(meetings_to_process))

    processed_count = 0

    for meeting in meetings_to_process:
        meeting_id = meeting["id"]
        meeting_title = meeting.get("title") or meeting_id

        try:
            logging.info("processing meeting %s", meeting_title)
            generate_notes_for_meeting(meeting_id)
            processed_count += 1
        except Exception as error:
            logging.exception(
                "failed to process meeting %s: %s",
                meeting_id,
                error,
            )

    logging.info("processed %s meetings", processed_count)
    return processed_count