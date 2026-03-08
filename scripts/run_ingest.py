from pathlib import Path

from meeting_ingestion.services.ingest import ingest_meetings


if __name__ == "__main__":
    inserted = ingest_meetings(
        base_path=Path("data/sample_meeting_transcripts"),
        source="manual",
        with_chunks=True,
    )

    print(f"inserted meetings: {inserted}")