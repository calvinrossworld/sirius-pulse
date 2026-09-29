"""Plan storage with Supabase first and local JSON fallback."""
import os
import json
import uuid
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = object

supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
PLAN_DIR = Path(__file__).parent / "plans"
PLAN_DIR.mkdir(exist_ok=True)

supabase: Client = None

if create_client is not None and supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)


def save_plan(data: dict) -> str:
    """Save plan and return its public id."""
    plan_id = str(uuid.uuid4())[:8]

    if supabase is not None:
        supabase.table("plans").insert({
            "id": plan_id,
            "artist_data": data.get("artist", {}),
            "plan_data": data.get("plan", {}),
            "pdf_url": None,
            "bios": data.get("bios", []),
            "email": data.get("email", ""),
        }).execute()
    else:
        _local_plan_path(plan_id).write_text(json.dumps(data, indent=2), encoding="utf-8")

    return plan_id


def get_plan(plan_id: str) -> dict | None:
    """Fetch plan from Supabase or local JSON storage by id."""
    if supabase is None:
        path = _local_plan_path(plan_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    resp = supabase.table("plans").select("*").eq("id", plan_id).execute()
    if not resp.data:
        return None

    row = resp.data[0]
    return {
        "artist": row["artist_data"],
        "plan": row["plan_data"],
        "bios": row.get("bios", []),
        "email": row.get("email", ""),
    }


def get_plan_by_email(email: str) -> dict | None:
    """Find the most recent plan for an email address."""
    if supabase is None:
        normalized = email.strip().lower()
        newest: tuple[float, str, dict] | None = None
        for path in PLAN_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("email", "").strip().lower() != normalized:
                continue
            current = (path.stat().st_mtime, path.stem, data)
            if newest is None or current[0] > newest[0]:
                newest = current
        if newest is None:
            return None
        _, plan_id, data = newest
        return {**data, "plan_id": plan_id}

    resp = supabase.table("plans").select("*").eq("email", email).order("id", desc=True).limit(1).execute()
    if not resp.data:
        return None
    row = resp.data[0]
    return {
        "artist": row["artist_data"],
        "plan": row["plan_data"],
        "bios": row.get("bios", []),
        "email": row.get("email", ""),
        "plan_id": row["id"],
    }


def email_exists(email: str) -> bool:
    """Check if an email already has a plan."""
    if supabase is None:
        return False
    resp = supabase.table("plans").select("id").eq("email", email).limit(1).execute()
    return len(resp.data) > 0


def update_plan_pdf_url(plan_id: str, pdf_url: str) -> None:
    """Update the pdf_url field for a plan."""
    if supabase is None:
        path = _local_plan_path(plan_id)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        data["pdf_url"] = pdf_url
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    supabase.table("plans").update({"pdf_url": pdf_url}).eq("id", plan_id).execute()


def _local_plan_path(plan_id: str) -> Path:
    return PLAN_DIR / f"{plan_id}.json"
