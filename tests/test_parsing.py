from meeting_ingestion.parsing import parse_meeting_from_path


def test_parse_full_filename(tmp_path):
    # create a temporary file with a full meeting filename format
    file = tmp_path / "AI TEAM MEETING - July 17 (37 mins).txt"
    file.write_text("dummy transcript")

    result = parse_meeting_from_path(file)

    # verify that title, date and duration are parsed correctly
    assert result.title == "AI TEAM MEETING"
    assert result.meeting_date.month == 7
    assert result.meeting_date.day == 17
    assert result.duration_mins == 37


def test_parse_without_duration(tmp_path):
    # create filename without duration section
    file = tmp_path / "AI TEAM MEETING - July 17.txt"
    file.write_text("dummy transcript")

    result = parse_meeting_from_path(file)

    # duration should be None when missing
    assert result.title == "AI TEAM MEETING"
    assert result.meeting_date.month == 7
    assert result.meeting_date.day == 17
    assert result.duration_mins is None


def test_parse_short_month_name(tmp_path):
    # create filename using short month name
    file = tmp_path / "AI TEAM MEETING - Jul 17 (20 mins).txt"
    file.write_text("dummy transcript")

    result = parse_meeting_from_path(file)

    # short month names should still parse correctly
    assert result.title == "AI TEAM MEETING"
    assert result.meeting_date.month == 7
    assert result.meeting_date.day == 17
    assert result.duration_mins == 20


def test_fallback_when_filename_does_not_match_pattern(tmp_path):
    # create filename that does not match expected pattern
    file = tmp_path / "random_filename.txt"
    file.write_text("dummy transcript")

    result = parse_meeting_from_path(file)

    # parser should fall back to filename and no duration
    assert result.title == "random_filename"
    assert result.duration_mins is None


def test_parse_filename_with_extra_whitespace(tmp_path):
    # create filename with inconsistent spacing
    file = tmp_path / "  AI   TEAM MEETING   -   July   17   (37 mins)  .txt"
    file.write_text("dummy transcript")

    result = parse_meeting_from_path(file)

    # parser should normalize whitespace
    assert result.title == "AI TEAM MEETING"
    assert result.meeting_date.month == 7
    assert result.meeting_date.day == 17
    assert result.duration_mins == 37


def test_parse_month_case_insensitive(tmp_path):
    # create filename with lowercase month
    file = tmp_path / "AI TEAM MEETING - july 17 (15 mins).txt"
    file.write_text("dummy transcript")

    result = parse_meeting_from_path(file)

    # month parsing should ignore case
    assert result.meeting_date.month == 7
    assert result.meeting_date.day == 17
    assert result.duration_mins == 15