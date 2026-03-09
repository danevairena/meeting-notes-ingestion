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
├─ chunking.py
├─ config.py
├─ docx_reader.py
├─ parsing.py
├─ supabase_client.py
├─ llm_client.py
│
├─ services/
│   ├─ ingest.py
│   ├─ extract_notes.py
│   ├─ process_all_meetings.py
│   └─ list_meetings.py
│
scripts/
│
├─ run_ingest.py
├─ run_list_meetings.py
├─ run_extract_notes.py
└─ run_process_all_meetings.py
│
tests/
```

## Module Responsibilities

Each module has a single responsibility:

- **docx_reader** — extracts transcript text from Word documents  
- **parsing** — parses meeting metadata from filenames  
- **chunking** — splits transcripts into overlapping text chunks  
- **supabase_client** — handles Supabase database connection  
- **llm_client** — handles communication with the Gemini API and structured LLM outputs  

### Services

- **services/ingest** — ingestion pipeline that reads DOCX files and stores transcripts and chunks in the database  
- **services/list_meetings** — retrieves stored meetings from the database  
- **services/extract_notes** — generates structured meeting notes using the LLM  
- **services/process_all_meetings** — batch processing for meetings that do not yet have notes  

### Scripts

- **run_ingest.py** — CLI runner for ingesting meeting transcripts  
- **run_list_meetings.py** — CLI runner for listing stored meetings  
- **run_extract_notes.py** — generates notes for a single meeting  
- **run_process_all_meetings.py** — generates notes for all meetings without notes  

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

The system uses Gemini structured outputs validated with a Pydantic schema.

Fields extracted:

- summary
- action_items
- key_takeaways
- topics
- next_steps

For long transcripts:

1. transcripts are split into chunks
2. each chunk is processed independently
3. results are merged
4. a final LLM call produces a clean meeting summary

---

## Prompt Strategy

We use a structured prompt instructing the LLM to extract meeting notes in a strict JSON schema.

The schema includes:

- summary
- action_items
- key_takeaways
- topics
- next_steps

The Gemini SDK validates the response against a **Pydantic schema (`MeetingNotes`)**, ensuring the returned structure matches the expected format.

Chunking is used for long transcripts to avoid context limits. Each chunk is processed independently and then merged.

---

## Output Validation and Normalization

The pipeline validates and cleans LLM outputs using several steps:

### 1. Schema validation
Structured outputs are validated using a Pydantic model.

### 2. Normalization
The pipeline removes:
- empty action items
- duplicated action items
- duplicated topics
- duplicated key takeaways

### 3. Edge case handling
The following edge cases are handled:

- transcript too short
- transcript too long (chunking)
- empty action items
- duplicated action items
- missing owners or due dates

### 4. Final summarization
For long transcripts, chunk summaries are merged and a final LLM call generates a clean meeting summary.

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