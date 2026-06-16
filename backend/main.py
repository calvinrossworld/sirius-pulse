"""Sirius Pulse — FastAPI backend."""
import os
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Path as PathParam
from pydantic import BaseModel
from typing import Optional

from generator import generate_plan
from pdf_builder import build_pdf

app = FastAPI(title="Sirius Pulse API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "pdfs"
PDF_DIR.mkdir(exist_ok=True)
PLANS_DIR = BASE_DIR / "plans"


def save_plan(data: dict) -> str:
    plan_id = str(uuid.uuid4())[:8]
    path = PLANS_DIR / f"{plan_id}.json"
    path.write_text(json.dumps(data, indent=2))
    return plan_id


def get_plan(plan_id: str) -> dict | None:
    path = PLANS_DIR / f"{plan_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


class GenerateRequest(BaseModel):
    stage_name: str
    genre: str
    subgenre: Optional[str] = ""
    career_stage: str
    platforms: list[str]
    promoting: str
    model_artists: Optional[str] = ""
    challenge: Optional[str] = ""


@app.post("/generate")
async def generate(request: GenerateRequest):
    try:
        plan = generate_plan(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    plan_id = save_plan({"artist": request.model_dump(), "plan": plan})

    return JSONResponse({"plan_id": plan_id})


@app.get("/plan/{plan_id}")
async def get_plan_route(plan_id: str = PathParam(..., description="Plan ID")):
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return JSONResponse(plan)


@app.get("/download/{plan_id}")
async def download_plan(plan_id: str = PathParam(..., description="Plan ID")):
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    artist_name = plan["artist"].get("stage_name", "Artist")
    pdf_path = PDF_DIR / f"{plan_id}.pdf"

    try:
        build_pdf(plan["plan"], artist_name, str(pdf_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF error: {str(e)}")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{artist_name}-SiriusPulse-Strategy.pdf",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)