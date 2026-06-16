"""Simple JSON file storage for plans."""
import json
import uuid
from pathlib import Path

STORAGE_DIR = Path(__file__).parent / "plans"
STORAGE_DIR.mkdir(exist_ok=True)

def save_plan(data: dict) -> str:
    plan_id = str(uuid.uuid4())[:8]
    path = STORAGE_DIR / f"{plan_id}.json"
    path.write_text(json.dumps(data, indent=2))
    return plan_id

def get_plan(plan_id: str) -> dict | None:
    path = STORAGE_DIR / f"{plan_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())