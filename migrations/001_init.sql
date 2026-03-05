create extension if not exists "pgcrypto";

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.meetings (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete set null,
  title text not null,
  meeting_date date not null,
  source text not null,
  source_file text not null,
  raw_transcript text not null,
  created_at timestamptz not null default now()
);

create unique index if not exists ux_meetings_source_file
on public.meetings(source_file);

create index if not exists ix_meetings_project_date
on public.meetings(project_id, meeting_date);

create table if not exists public.notes (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid not null references public.meetings(id) on delete cascade,
  summary text,
  action_items jsonb,
  key_takeaways jsonb,
  topics jsonb,
  next_steps jsonb,
  created_at timestamptz not null default now()
);

create index if not exists ix_notes_meeting_id
on public.notes(meeting_id);

create table if not exists public.transcript_chunks (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid not null references public.meetings(id) on delete cascade,
  chunk_index int not null,
  content text not null,
  created_at timestamptz not null default now(),
  unique(meeting_id, chunk_index)
);

create index if not exists ix_chunks_meeting
on public.transcript_chunks(meeting_id);