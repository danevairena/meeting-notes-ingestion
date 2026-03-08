from meeting_ingestion.services.list_meetings import list_meetings


if __name__ == "__main__":
    meetings = list_meetings()

    for meeting in meetings:
        print(f"{meeting['id']} | {meeting['meeting_date']} | {meeting['title']}")