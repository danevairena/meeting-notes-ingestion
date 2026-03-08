import pytest
from pathlib import Path
from unittest.mock import MagicMock

from meeting_ingestion.services.ingest import _process_file


def test_process_file_inserts_meeting_and_chunks(monkeypatch):
    # fake parsed meeting
    class FakeParsed:
        title = "AI TEAM MEETING"
        meeting_date = type("Date", (), {"isoformat": lambda self: "2024-07-17"})()

    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.parse_meeting_from_path",
        lambda _: FakeParsed(),
    )

    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.read_docx",
        lambda _: "some transcript text",
    )

    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.chunk_text",
        lambda _: ["chunk one", "chunk two"],
    )

    # first execute call for meetings upsert
    fake_meeting_result = MagicMock()
    fake_meeting_result.data = [{"id": "meeting-123"}]

    fake_meeting_query = MagicMock()
    fake_meeting_query.execute.return_value = fake_meeting_result

    fake_meeting_table = MagicMock()
    fake_meeting_table.upsert.return_value = fake_meeting_query

    # second table call for transcript_chunks
    fake_chunk_result = MagicMock()
    fake_chunk_result.data = [{"id": "chunk-1"}]

    fake_chunk_query = MagicMock()
    fake_chunk_query.execute.return_value = fake_chunk_result

    fake_chunk_table = MagicMock()
    fake_chunk_table.upsert.return_value = fake_chunk_query

    fake_supabase = MagicMock()
    fake_supabase.table.side_effect = [fake_meeting_table, fake_chunk_table]

    result = _process_file(
        file_path=Path("meeting.docx"),
        supabase=fake_supabase,
        source="manual",
        with_chunks=True,
    )

    assert result is True


def test_process_file_skips_empty_transcript(monkeypatch):
    # fake parsed meeting
    class FakeParsed:
        title = "AI TEAM MEETING"
        meeting_date = type("Date", (), {"isoformat": lambda self: "2024-07-17"})()

    # mock parsing
    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.parse_meeting_from_path",
        lambda _: FakeParsed(),
    )

    # return empty transcript
    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.read_docx",
        lambda _: "   ",
    )

    fake_supabase = MagicMock()

    result = _process_file(
        file_path=Path("meeting.docx"),
        supabase=fake_supabase,
        source="manual",
        with_chunks=True,
    )

    # function should skip the file
    assert result is False


def test_process_file_handles_insert_failure(monkeypatch):
    # fake parsed meeting
    class FakeParsed:
        title = "AI TEAM MEETING"
        meeting_date = type("Date", (), {"isoformat": lambda self: "2024-07-17"})()

    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.parse_meeting_from_path",
        lambda _: FakeParsed(),
    )

    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.read_docx",
        lambda _: "some transcript",
    )

    monkeypatch.setattr(
        "meeting_ingestion.services.ingest.chunk_text",
        lambda _: [],
    )

    # mock supabase chain: table -> upsert -> execute
    fake_result = MagicMock()
    fake_result.data = []

    fake_query = MagicMock()
    fake_query.execute.return_value = fake_result

    fake_table = MagicMock()
    fake_table.upsert.return_value = fake_query

    fake_supabase = MagicMock()
    fake_supabase.table.return_value = fake_table

    result = _process_file(
        file_path=Path("meeting.docx"),
        supabase=fake_supabase,
        source="manual",
        with_chunks=True,
    )

    assert result is False