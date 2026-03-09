import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .config import config

# schema for a single action item extracted from the meeting
class ActionItem(BaseModel):
    text: str
    owner: str | None = None
    due_date: str | None = None

# schema for a next step item
class NextStep(BaseModel):
    text: str
    owner: str | None = None

# main structured output schema returned by the llm
class MeetingNotes(BaseModel):
    summary: str
    action_items: list[ActionItem] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)

# schema used for cleaned meeting notes returned by the rewrite step
class CleanMeetingNotes(BaseModel):
    summary: str
    action_items: list[ActionItem] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)

# prompt that instructs the llm how to extract structured meeting notes
PROMPT = """
Extract structured meeting notes from the transcript.

Return structured data following this schema:

{
  "summary": string,
  "action_items": [
    { "text": string, "owner": string | null, "due_date": string | null }
  ],
  "key_takeaways": [string],
  "topics": [string],
  "next_steps": [
    { "text": string, "owner": string | null }
  ]
}

Rules:
- Do not invent information.
- If owner is unknown, use null.
- If due_date is unknown, use null.
- Summary should be concise (2–5 sentences).
- Remove duplicate action items.
- If the transcript is very short or unclear, return empty lists.
"""

# prompt for generating one final summary from chunk summaries
FINAL_SUMMARY_PROMPT = """
You are given multiple partial summaries from different chunks of the same meeting.

Write one final clean meeting summary in 3 to 5 sentences.

Rules:
- combine overlapping information
- remove repetition
- keep only the most important points
- do not invent information
- return plain text only
"""

# prompt used to rewrite and compress structured meeting notes
REWRITE_PROMPT = """
You are refining structured meeting notes.

You will receive meeting notes that were automatically extracted from a transcript.
They may contain duplicated information, overly detailed items, or loosely defined tasks.

Your job is to rewrite and clean the notes so they are clear, concise, and suitable for a final meeting summary document.

Return the output using the same JSON schema:

{
  "summary": string,
  "action_items": [
    { "text": string, "owner": string | null, "due_date": string | null }
  ],
  "key_takeaways": [string],
  "topics": [string],
  "next_steps": [
    { "text": string, "owner": string | null }
  ]
}

IMPORTANT RULES

1. Do NOT invent information.
2. Do NOT remove valid tasks that appear in the input.
3. Do NOT change the meaning of decisions made in the meeting.
4. Preserve important names, numbers, tools, products, or constraints mentioned in the notes.
5. The output should help someone who did NOT attend the meeting understand what happened.

Summary
- Rewrite the summary into 2–4 clear sentences.
- Focus on the main purpose of the meeting, the key discussions, and the main outcomes.
- Remove small or repetitive details.
- Preserve important decisions or constraints.

Action Items
- Include only tasks that someone is expected to perform.
- Each task should be written as a clear instruction starting with a verb.
- Example: "Review the campaign email templates".
- If the owner is unknown, set owner to null.
- Do NOT remove a valid task unless it is clearly duplicated.
- Maximum 5 items.

Key Takeaways
- Include the most important insights or conclusions from the meeting.
- Prefer statements that describe decisions, lessons, or important observations.
- Avoid repeating the same idea in different wording.
- Maximum 5 items.

Topics
- Group related discussion areas together.
- Use descriptive phrases instead of single words.
- Topics should represent major discussion areas, not small details.
- Maximum 3–5 topics.

Next Steps
- Represent follow-up work or strategic continuation of the discussion.
- They may involve the team rather than a single owner.
- Do NOT duplicate action items.
- Maximum 5 items.

Cleaning Rules
- Remove duplicates and near-duplicates.
- Merge items that express the same idea.
- Prefer clarity over completeness.
- Keep wording simple and direct.

Quality Check Before Returning
Before producing the final JSON, verify:

- Action items are real tasks.
- No section contains meaningless filler.
- No information contradicts another section.
- Important details (names, tools, decisions) were not accidentally removed.

Return ONLY valid JSON.
Do not include explanations.
"""

# initialize gemini client using api key from config
client = genai.Client(api_key=config.GEMINI_API_KEY)

# send transcript to the llm and return structured notes plus raw model output
def extract_notes(transcript: str) -> tuple[dict[str, object], str]:

    # call gemini model with structured output schema
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=f"{PROMPT}\n\nTranscript:\n{transcript}",
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=MeetingNotes,
        ),
    )

    # parsed contains the validated pydantic object returned by the sdk
    parsed = response.parsed

    if parsed is None:
        raise ValueError("Gemini returned invalid structured output")

    # keep raw llm output for debugging or storage in llm_raw column
    raw_llm = response.text or json.dumps(parsed.model_dump(), ensure_ascii=False)

    # return structured notes as dict and the raw llm response
    return parsed.model_dump(), raw_llm

# generate one final summary from multiple chunk summaries
def generate_final_summary(summaries: list[str]) -> str:
    cleaned_summaries = [summary.strip() for summary in summaries if summary.strip()]
    if not cleaned_summaries:
        return ""

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=(
            f"{FINAL_SUMMARY_PROMPT}\n\n"
            f"Chunk summaries:\n" + "\n".join(f"- {summary}" for summary in cleaned_summaries)
        ),
        config=types.GenerateContentConfig(
            temperature=0,
        ),
    )

    return (response.text or "").strip()

# rewrite merged notes using llm to remove noise and duplicates
def rewrite_notes(notes: dict[str, object]) -> tuple[dict[str, object], str]:
    raw_input = json.dumps(notes, ensure_ascii=False, indent=2)

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=f"{REWRITE_PROMPT}\n\nMeeting notes:\n{raw_input}",
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=CleanMeetingNotes,
        ),
    )

    parsed = response.parsed
    if parsed is None:
        raise ValueError("Gemini returned invalid rewritten notes")

    raw_llm = response.text or json.dumps(parsed.model_dump(), ensure_ascii=False)
    return parsed.model_dump(), raw_llm