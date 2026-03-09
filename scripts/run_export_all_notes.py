import logging

from meeting_ingestion.services.export_notes import export_all_notes


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    exported_files = export_all_notes()

    logging.info("exported %s files", len(exported_files))
    for file_path in exported_files:
        logging.info("exported %s", file_path)


if __name__ == "__main__":
    main()