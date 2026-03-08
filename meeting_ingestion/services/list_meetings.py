from ..supabase_client import get_supabase_client


def list_meetings() -> list[dict]:
    # fetch meetings ordered by date
    supabase = get_supabase_client()

    result = (
        supabase.table("meetings")
        .select("id,title,meeting_date")
        .order("meeting_date")
        .execute()
    )

    return result.data or []