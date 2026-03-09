import argparse
import logging

from meeting_ingestion.services.extract_notes import generate_notes_for_meeting


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("meeting_id")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    result = generate_notes_for_meeting(args.meeting_id)
    logging.info("notes generated for meeting %s", result["meeting_id"])


if __name__ == "__main__":
    main()