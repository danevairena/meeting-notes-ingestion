# Meeting Notes Ingestion Pipeline

A Python-based ingestion pipeline for processing meeting transcripts stored as `.docx` files and loading them into a Supabase PostgreSQL database.

The system extracts transcript text, parses meeting metadata from filenames, associates meetings with projects based on folder structure, and stores both full transcripts and smaller text chunks for downstream processing.

---

# Features

- Extracts transcript text from `.docx` meeting files
- Parses meeting metadata (title, date, duration) from filenames
- Automatically resolves project names from folder structure
- Stores meetings and transcripts in Supabase
- Splits transcripts into overlapping chunks for further processing
- Prevents duplicate ingestion using unique constraints
- Includes unit tests for parsing, chunking, and ingestion logic

---

# Architecture

The ingestion pipeline follows a modular structure:

docx transcripts
↓
docx_reader → extract text
↓
parsing → parse filename metadata
↓
ingestion service → store meeting
↓
chunking → split transcript
↓
database → store transcript chunks

---

# Project Structure

meeting_ingestion/
    chunking.py
    config.py
    docx_reader.py
    parsing.py
    supabase_client.py
    services/
        ingest.py
        list_meetings.py

scripts/
    run_ingest.py
    run_list_meetings.py

tests/

Each module has a single responsibility:

- **docx_reader** — extracts transcript text from Word documents
- **parsing** — parses meeting metadata from filenames
- **chunking** — splits transcripts into overlapping text chunks
- **supabase_client** — handles database connection
- **services/ingest** — ingestion pipeline logic
- **services/list_meetings** — query service for stored meetings

---

# Database Schema

The project uses Supabase (PostgreSQL) with four main tables.

### projects

Stores project names derived from folder structure.

| column | type |
|------|------|
id | uuid |
name | text |
created_at | timestamptz |

---

### meetings

Stores meeting metadata and full transcript.

| column | type |
|------|------|
id | uuid |
project_id | uuid |
title | text |
meeting_date | date |
source | text |
source_file | text |
raw_transcript | text |
created_at | timestamptz |

`source_file` has a unique index to prevent duplicate ingestion.

---

### transcript_chunks

Stores transcript split into smaller chunks.

| column | type |
|------|------|
id | uuid |
meeting_id | uuid |
chunk_index | int |
content | text |
created_at | timestamptz |

Each chunk is uniquely identified by `(meeting_id, chunk_index)`.

---

### notes

Reserved for structured summaries of meetings.

| column | type |
|------|------|
id | uuid |
meeting_id | uuid |
summary | text |
action_items | jsonb |
key_takeaways | jsonb |
topics | jsonb |
next_steps | jsonb |

---

# Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd meeting-notes-ingestion
```

2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

Create a .env file

SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

---

# Running the Ingestion Pipeline

### Place meeting transcripts in:

data/sample_meeting_transcripts/

Example:

data/sample_meeting_transcripts/
    edamame/
        AI TEAM MEETING - July 17 (37 mins).docx

    gatekeeper/
        Gatekeeper - November 26 (33 mins).docx

### Run ingestion:

python -m scripts.run_ingest

The script will:
1. scan all .docx files
2. extract transcript text
3. parse meeting metadata
4. create projects based on folder names
5. insert meetings into the database
6. generate transcript chunks

---

# Listing Stored Meetings

```bash
python -m scripts.run_list_meetings
```

Example output:

21cb118a | 2025-05-15 | AI TEAM MEETING
8fa5ffa1 | 2025-09-04 | Team update

---

# Running Tests

```bash
pytest
```

Tests cover:
- filename parsing
- transcript chunking
- ingestion logic

---

# Design Notes

Projects are derived from the folder structure containing transcript files.

Example:
data/sample_meeting_transcripts/edamame/meeting.docx
→ project = edamame

Meetings use a unique constraint on source_file so ingestion can run multiple times without creating duplicates.

Meeting year is inferred from file metadata when filenames do not contain a year. If the resulting date falls in the future, the parser adjusts the year to the previous year.

---

#  Author

Irena Daneva
GitHub: https://github.com/danevairena

---

# Project Purpose

This project is part of my backend developer portfolio and demonstrates the design and implementation of a small data ingestion pipeline in Python.

The goal of the project is to process meeting transcripts stored as `.docx` files and load them into a structured PostgreSQL database hosted on Supabase.

It showcases practical backend development skills including:

- file processing and text extraction
- metadata parsing from filenames
- database schema design
- building an ingestion pipeline
- writing modular and testable Python code
- implementing unit tests with pytest
- designing idempotent data ingestion workflows

The project simulates a simplified backend service responsible for preparing meeting data for further processing such as summarization, analytics, or semantic search.