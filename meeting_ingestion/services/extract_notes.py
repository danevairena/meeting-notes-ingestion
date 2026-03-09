import logging

from ..llm_client import extract_notes, generate_final_summary, rewrite_notes
from ..supabase_client import get_supabase_client


# load a single meeting row by id
def _get_meeting(meeting_id: str) -> dict:
    supabase = get_supabase_client()

    result = (
        supabase.table("meetings")
        .select("id,title,raw_transcript")
        .eq("id", meeting_id)
        .limit(1)
        .execute()
    )

    rows = result.data or []
    if not rows:
        raise ValueError(f"meeting not found: {meeting_id}")

    return rows[0]


# load stored transcript chunks for a meeting
def _get_transcript_chunks(meeting_id: str) -> list[str]:
    supabase = get_supabase_client()

    result = (
        supabase.table("transcript_chunks")
        .select("chunk_index,content")
        .eq("meeting_id", meeting_id)
        .order("chunk_index")  
        .execute()
    )

    rows = result.data or []
    return [row["content"] for row in rows if row.get("content")]


# remove empty or duplicate action items
def _remove_duplicates_action_items(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduplicated: list[dict] = []

    for item in items:
        text = (item.get("text") or "").strip()
        if not text:
            continue

        key = text.lower()
        if key in seen:
            continue

        seen.add(key)
        deduplicated.append(
            {
                "text": text,
                "owner": item.get("owner"),
                "due_date": item.get("due_date"),
            }
        )

    return deduplicated


# remove empty or duplicate next steps
def _remove_duplicates_next_steps(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduplicated: list[dict] = []

    for item in items:
        text = (item.get("text") or "").strip()
        if not text:
            continue

        key = text.lower()
        if key in seen:
            continue

        seen.add(key)
        deduplicated.append(
            {
                "text": text,
                "owner": item.get("owner"),
            }
        )

    return deduplicated


# normalize llm output into a db-safe structure
def _normalize_notes(data: dict[str, object]) -> dict[str, object]:
    action_items = data.get("action_items") or []
    next_steps = data.get("next_steps") or []

    return {
        "summary": str(data.get("summary") or "").strip(),
        "action_items": _remove_duplicates_action_items(action_items),
        "key_takeaways": list(dict.fromkeys(data.get("key_takeaways") or [])),
        "topics": list(dict.fromkeys(data.get("topics") or [])),
        "next_steps": _remove_duplicates_next_steps(next_steps),
    }


# merge multiple chunk-level note outputs into one result
def _merge_chunk_notes(results: list[dict[str, object]]) -> dict[str, object]:
    summaries: list[str] = []
    action_items: list[dict] = []
    key_takeaways: list[str] = []
    topics: list[str] = []
    next_steps: list[dict] = []

    # collect summaries and structured fields from each chunk
    for result in results:
        summary = str(result.get("summary") or "").strip()
        if summary:
            summaries.append(summary)

        # merge action items, takeaways, topics, and next steps from all chunks
        action_items.extend(result.get("action_items") or [])
        key_takeaways.extend(result.get("key_takeaways") or [])
        topics.extend(result.get("topics") or [])
        next_steps.extend(result.get("next_steps") or [])

    # reuse the single summary or generate a final summary from multiple chunk summaries
    if len(summaries) == 1:
        final_summary = summaries[0]
    else:
        final_summary = generate_final_summary(summaries)

    merged_notes = {
        "summary": final_summary,
        "action_items": _remove_duplicates_action_items(action_items),
        # deduplicate simple list fields while preserving order
        "key_takeaways": list(
            dict.fromkeys(s.strip() for s in key_takeaways if s.strip())
        ),
        "topics": list(
            dict.fromkeys(s.strip() for s in topics if s.strip())
        ),
        "next_steps": _remove_duplicates_next_steps(next_steps),
    }

    # run final rewrite pass to clean and compress notes
    cleaned_notes, _ = rewrite_notes(merged_notes)
    return cleaned_notes


# generate notes for one meeting and save them in the notes table
def generate_notes_for_meeting(meeting_id: str) -> dict:
    supabase = get_supabase_client()
    meeting = _get_meeting(meeting_id)

    transcript = (meeting.get("raw_transcript") or "").strip()
    if not transcript:
        raise ValueError(f"meeting {meeting_id} has empty transcript")

    # handle very short transcripts without calling the llm
    if len(transcript.split()) < 40:
        structured = {
            "summary": "Transcript is too short to extract reliable structured notes.",
            "action_items": [],
            "key_takeaways": [],
            "topics": [],
            "next_steps": [],
        }
        raw_llm = ""
    else:
        chunks = _get_transcript_chunks(meeting_id)
        logging.info("Processing %s transcript chunks for meeting %s", len(chunks), meeting_id)

        if not chunks:
            chunks = [transcript]

        # single chunk case
        if len(chunks) == 1:
            structured, raw_llm = extract_notes(transcript)
            structured = _normalize_notes(structured)

        # multi-chunk case
        else:
            chunk_results: list[dict[str, object]] = []
            raw_parts: list[str] = []

            for chunk in chunks:
                chunk_notes, chunk_raw = extract_notes(chunk)
                chunk_results.append(_normalize_notes(chunk_notes))
                raw_parts.append(chunk_raw)

            structured = _merge_chunk_notes(chunk_results)
            raw_llm = "\n\n---chunk---\n\n".join(raw_parts)

    payload = {
        "meeting_id": meeting_id,
        "summary": structured["summary"],
        "action_items": structured["action_items"],
        "key_takeaways": structured["key_takeaways"],
        "topics": structured["topics"],
        "next_steps": structured["next_steps"],
        "llm_raw": raw_llm,
    }

    result = (
        supabase.table("notes")
        .upsert(payload, on_conflict="meeting_id")
        .execute()
    )

    rows = result.data or []
    if not rows:
        raise ValueError(f"Failed to store notes for meeting: {meeting_id}")

    logging.info("Stored notes for meeting %s", meeting_id)
    return rows[0]