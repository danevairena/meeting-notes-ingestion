import logging

from meeting_ingestion.services.process_all_meetings import (
    process_all_meetings_without_notes,
)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    # reduce noisy logs from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)

    process_all_meetings_without_notes()


if __name__ == "__main__":
    main()