"""Supabase-backed storage for plans."""
import os
from supabase import create_client, Client

supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase: Client = None

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)


def save_plan(data: dict) -> str:
    """Save plan to Supabase. Returns plan_id."""
    if supabase is None:
        raise RuntimeError("Supabase not configured")
    import uuid
    plan_id = str(uuid.uuid4())[:8]
    supabase.table("plans").insert({
        "id": plan_id,
        "artist_data": data["artist"],
        "plan_data": data["plan"],
        "pdf_url": None,
    }).execute()
    return plan_id


def get_plan(plan_id: str) -> dict | None:
    """Fetch plan from Supabase by id."""
    if supabase is None:
        raise RuntimeError("Supabase not configured")
    resp = supabase.table("plans").select("*").eq("id", plan_id).execute()
    if not resp.data:
        return None
    row = resp.data[0]
    return {"artist": row["artist_data"], "plan": row["plan_data"]}


def update_plan_pdf_url(plan_id: str, pdf_url: str) -> None:
    """Update the pdf_url field for a plan."""
    if supabase is None:
        raise RuntimeError("Supabase not configured")
    supabase.table("plans").update({"pdf_url": pdf_url}).eq("id", plan_id).execute()
