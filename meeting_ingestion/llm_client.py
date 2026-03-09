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