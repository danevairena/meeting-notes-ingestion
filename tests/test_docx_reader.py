from pathlib import Path
from meeting_ingestion.docx_reader import read_docx


def main():
    # find all transcript files
    base_path = Path("data/sample_meeting_transcripts")
    files = sorted(base_path.rglob("*.docx"))

    print("found files:", len(files))

    for file_path in files:
        transcript = read_docx(file_path)

        print()
        print("file:", file_path.name)
        print("chars:", len(transcript))
        print("preview:", transcript[:300])


if __name__ == "__main__":
    main()