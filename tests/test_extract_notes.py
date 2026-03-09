from meeting_ingestion.services.extract_notes import _merge_chunk_notes


def test_merge_chunk_notes_deduplicates_and_uses_final_summary(monkeypatch):
    def fake_generate_final_summary(summaries: list[str]) -> str:
        assert summaries == [
            "The team discussed launch plans.",
            "They also reviewed testing and pricing.",
        ]
        return "Final merged summary"

    monkeypatch.setattr(
        "meeting_ingestion.services.extract_notes.generate_final_summary",
        fake_generate_final_summary,
    )

    results = [
        {
            "summary": "The team discussed launch plans.",
            "action_items": [
                {
                    "text": "Prepare launch checklist",
                    "owner": "Ivan",
                    "due_date": None,
                }
            ],
            "key_takeaways": ["Launch is planned soon", "Testing is important"],
            "topics": ["Launch", "Testing"],
            "next_steps": [
                {
                    "text": "Run beta test",
                    "owner": "Maria",
                }
            ],
        },
        {
            "summary": "They also reviewed testing and pricing.",
            "action_items": [
                {
                    "text": "prepare launch checklist",
                    "owner": "Ivan",
                    "due_date": None,
                }
            ],
            "key_takeaways": ["Testing is important", "Pricing needs validation"],
            "topics": ["Testing", "Pricing"],
            "next_steps": [
                {
                    "text": "Run beta test",
                    "owner": "Maria",
                }
            ],
        },
    ]

    merged = _merge_chunk_notes(results)

    assert merged["summary"] == "Final merged summary"
    assert merged["action_items"] == [
        {
            "text": "Prepare launch checklist",
            "owner": "Ivan",
            "due_date": None,
        }
    ]
    assert merged["key_takeaways"] == [
        "Launch is planned soon",
        "Testing is important",
        "Pricing needs validation",
    ]
    assert merged["topics"] == ["Launch", "Testing", "Pricing"]
    assert merged["next_steps"] == [
        {
            "text": "Run beta test",
            "owner": "Maria",
        }
    ]