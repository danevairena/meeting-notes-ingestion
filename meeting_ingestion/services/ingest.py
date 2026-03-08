import logging
from pathlib import Path

from ..chunking import chunk_text
from ..docx_reader import read_docx
from ..parsing import parse_meeting_from_path
from ..supabase_client import get_supabase_client


def _process_file(file_path: Path, supabase, source: str, with_chunks: bool) -> bool:
    # process a single transcript file and store it in the database

    parsed = parse_meeting_from_path(file_path)
    transcript = read_docx(file_path)

    if not transcript.strip():
        logging.warning("Skipping empty transcript: %s", file_path.name)
        return False

    meeting_payload = {
        "title": parsed.title,
        "meeting_date": parsed.meeting_date.isoformat(),
        "source": source,
        "source_file": str(file_path),
        "raw_transcript": transcript,
    }

    result = (
        supabase.table("meetings")
        .upsert(meeting_payload, on_conflict="source_file")
        .execute()
    )

    rows = result.data or []

    if not rows:
        logging.warning("Failed to insert meeting: %s", file_path.name)
        return False

    meeting_id = rows[0]["id"]
    logging.info("Stored meeting %s", meeting_id)

    if with_chunks:
        # split transcript into overlapping chunks
        chunks = chunk_text(transcript)

        if chunks:
            chunk_rows = [
                {
                    "meeting_id": meeting_id,
                    "chunk_index": i,
                    "content": chunk,
                }
                for i, chunk in enumerate(chunks)
            ]

            supabase.table("transcript_chunks").upsert(
                chunk_rows,
                on_conflict="meeting_id,chunk_index",
            ).execute()

            logging.info("Stored %s chunks", len(chunks))

    return True


# ingest all docx meeting transcripts from the given folder tree
def ingest_meetings(base_path: Path, source: str = "manual", with_chunks: bool = True) -> int:
    
    supabase = get_supabase_client()

    # find all transcript files recursively
    files = sorted(base_path.rglob("*.docx"))

    if not files:
        logging.warning("No docx files found in %s", base_path)
        return 0

    inserted_count = 0

    for file_path in files:
        logging.info("Processing file: %s", file_path)

        if _process_file(file_path, supabase, source, with_chunks):
            inserted_count += 1

    logging.info("Finished ingesting %s meetings", inserted_count)
    return inserted_count