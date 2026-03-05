from meeting_ingestion.supabase_client import get_supabase_client

def main():
    supabase = get_supabase_client()
    res = supabase.table("meetings").select("id").limit(1).execute()
    print(res.data)

if __name__ == "__main__":
    main()