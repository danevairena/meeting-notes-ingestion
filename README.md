# Meeting Notes Ingestion & LLM Extraction Pipeline

A Python-based backend pipeline for ingesting meeting transcripts (`.docx`), storing them in Supabase, and generating structured meeting notes using the Gemini API.

The system extracts transcript text, parses meeting metadata, stores transcripts and chunks in PostgreSQL, and generates structured meeting insights using an LLM.

---

# Features

- Extract transcript text from `.docx` files
- Parse meeting metadata from filenames
- Automatically derive projects from folder structure
- Store meetings and transcripts in Supabase
- Split transcripts into overlapping chunks
- Generate structured meeting notes using an LLM
- Batch process meetings without notes
- Prevent duplicate ingestion using database constraints
- Store raw LLM output for debugging
- Unit tests for parsing, chunking, ingestion, and note extraction

---


# System Architecture

The system consists of two pipelines.

## 1. Ingestion Pipeline

DOCX transcript  
↓  
docx_reader → extract transcript text  
↓  
parsing → parse filename metadata  
↓  
ingestion service → store meeting  
↓  
chunking → split transcript  
↓  
database → store transcript chunks

---

## 2. LLM Extraction Pipeline

transcript_chunks  
↓  
LLM extraction per chunk  
↓  
merge structured outputs  
↓  
final LLM summary  
↓  
notes table

---

# Project Structure

```
meeting_ingestion/
│
├─ __init__.py
├─ chunking.py
├─ config.py
├─ docx_reader.py
├─ parsing.py
├─ supabase_client.py
├─ llm_client.py
│
├─ services/
│   ├─ __init__.py
│   ├─ ingest.py
│   ├─ extract_notes.py
│   ├─ export_notes.py
│   ├─ list_meetings.py
│   └─ process_all_meetings.py
│
├─ migrations/
│   ├─ 001_init.sql
│   └─ 002_update_notes_for_llm_pipeline.sql
│
scripts/
│
├─ run_ingest.py
├─ run_list_meetings.py
├─ run_extract_notes.py
├─ run_process_all_meetings.py
├─ run_export_all_notes.py
├─ test_connection.py
└─ test_gemini.py
│
tests/
│
├─ test_chunking.py
├─ test_docx_reader.py
├─ test_extract_notes.py
├─ test_ingest.py
└─ test_parsing.py
```

---

# Module Responsibilities

Each module has a **single responsibility**, following a modular pipeline architecture.

## Core Modules

- **docx_reader** — extracts transcript text from Word (`.docx`) meeting files  
- **parsing** — parses meeting metadata (title, date, etc.) from filenames  
- **chunking** — splits long transcripts into overlapping chunks for LLM processing  
- **supabase_client** — manages the Supabase database connection  
- **llm_client** — communicates with the Gemini API and handles structured LLM outputs  

---

# Services

The `services` layer contains the main application pipelines.

- **services/ingest**  
  Reads DOCX files, extracts transcripts, and stores meetings and transcript chunks in the database.

- **services/list_meetings**  
  Retrieves stored meetings from the database.

- **services/extract_notes**  
  Runs the LLM extraction pipeline to generate structured meeting notes:
  - summary  
  - action items  
  - key takeaways  
  - topics  
  - next steps  

- **services/process_all_meetings**  
  Batch processing pipeline that generates notes for all meetings that do not yet have notes.

- **services/export_notes**  
  Exports generated meeting notes into structured **DOCX files**, grouped by project.

---

# Scripts

The `scripts` directory contains CLI entry points used to run different parts of the pipeline.

- **run_ingest.py** — ingest meeting transcripts from DOCX files  
- **run_list_meetings.py** — list meetings stored in the database  
- **run_extract_notes.py** — generate notes for a single meeting  
- **run_process_all_meetings.py** — generate notes for all meetings without notes  
- **run_export_all_notes.py** — export generated notes into DOCX files  

Utility scripts:

- **test_connection.py** — verifies database connectivity  
- **test_gemini.py** — tests Gemini API integration

---

# Tests

The `tests` directory contains unit tests for the core pipeline components.

- **test_chunking.py** — tests transcript chunking logic  
- **test_docx_reader.py** — tests DOCX transcript extraction  
- **test_extract_notes.py** — tests meeting note extraction and merging  
- **test_ingest.py** — tests the ingestion pipeline  
- **test_parsing.py** — tests metadata parsing from filenames

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
llm_raw | text |

`meeting_id` has a unique index to prevent duplicate ingestion.

---

# Setup

## Clone repository

```bash
git clone <repo-url>
cd meeting-notes-ingestion
```

## Create virtual environment

```bash
python -m venv .venv
```

Activate:

Windows

```bash
.venv\Scripts\activate
```

Mac/Linux

```bash
source .venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Configure environment variables

Create `.env`:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite
```

---

# Running the Pipelines

## Ingest transcripts

```bash
python -m scripts.run_ingest
```

## List stored meetings

```bash
python -m scripts.run_list_meetings
```

## Generate notes for one meeting

```bash
python -m scripts.run_extract_notes <meeting_id>
```

## Generate notes for all meetings without notes

```bash
python -m scripts.run_process_all_meetings
```

---

# LLM Extraction Strategy

The system uses **Gemini structured outputs** validated with a **Pydantic schema**.

## Fields extracted

- summary
- action_items
- key_takeaways
- topics
- next_steps

## Handling Long Transcripts

For long transcripts:

1. The transcript is split into smaller chunks.
2. Each chunk is processed independently by the LLM.
3. The results are merged into a single structured result.
4. A final LLM rewrite step produces a clean and consistent meeting notes document.

---

# Prompt Strategy

We use a structured prompt that instructs the LLM to extract meeting notes following a **strict JSON schema**.

The schema includes:

- summary
- action_items
- key_takeaways
- topics
- next_steps

The **Gemini SDK validates the response using a Pydantic schema (`MeetingNotes`)**, ensuring that the returned structure matches the expected format.

Chunking is used for long transcripts to avoid context limits. Each chunk is processed independently and then merged.

---

# Output Validation and Normalization

The pipeline validates and cleans LLM outputs using several steps.

## 1. Schema validation

Structured outputs are validated using a **Pydantic model**, ensuring that all required fields exist and follow the expected structure.

## 2. Normalization

The pipeline removes:

- empty action items
- duplicated action items
- duplicated topics
- duplicated key takeaways

This ensures the structured data remains clean and consistent.

## 3. Edge case handling

The pipeline explicitly handles several edge cases:

- transcript too short
- transcript too long (chunking)
- empty action items
- duplicated action items
- missing owners or due dates

## 4. Final rewrite and summarization

After merging chunk-level notes, a **final LLM rewrite step** is applied.

This step improves readability and removes redundant information while preserving the structured format.

The rewrite stage ensures that:

- the summary is concise and readable
- action items are clearly phrased as tasks
- duplicated or overly detailed items are removed
- topics are grouped into broader categories
- the output remains consistent with the defined JSON schema

---

## Running the Pipeline

### Process a single meeting

```bash
python -m scripts.run_extract_notes <meeting_id>
```

### Process all meetings without notes

```bash
python -m scripts.run_process_all_meetings
```

---

## Tests

Run all tests:

```bash
pytest
```

Lint the project:

```bash
ruff check .
```

---

## Database

Results are stored in the `notes` table:

- summary
- action_items (jsonb)
- key_takeaways (jsonb)
- topics (jsonb)
- next_steps (jsonb)
- llm_raw (raw LLM response)

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