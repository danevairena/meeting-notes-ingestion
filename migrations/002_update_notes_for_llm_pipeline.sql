alter table public.notes
add column if not exists llm_raw text;

create unique index if not exists idx_notes_meeting
on public.notes(meeting_id);