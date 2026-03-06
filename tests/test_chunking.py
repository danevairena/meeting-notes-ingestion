from meeting_ingestion.chunking import chunk_text


def test_empty_text_returns_empty_list():
    # empty input should return no chunks
    result = chunk_text("")
    assert result == []


def test_single_chunk_when_text_is_small():
    # text smaller than chunk_size should produce one chunk
    text = "one two three four five"

    result = chunk_text(text, chunk_size=10, overlap=2)

    assert len(result) == 1
    assert result[0] == text


def test_multiple_chunks_created():
    # large text should be split into multiple chunks
    text = " ".join([f"word{i}" for i in range(50)])

    result = chunk_text(text, chunk_size=10, overlap=2)

    assert len(result) > 1


def test_overlap_between_chunks():
    # overlapping words should appear in adjacent chunks
    text = " ".join([f"word{i}" for i in range(30)])

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    first_chunk_words = chunks[0].split()
    second_chunk_words = chunks[1].split()

    assert first_chunk_words[-2:] == second_chunk_words[:2]