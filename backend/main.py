"""Sirius Pulse — FastAPI backend with Supabase storage."""
import os
import json
import uuid
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Path as PathParam
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from generator import generate_plan
from pdf_builder import build_pdf
from storage import save_plan, get_plan, update_plan_pdf_url
from auditor import audit_profiles
from bio import generate_bios
from email import send_strategy_email

app = FastAPI(title="Sirius Pulse API", version="1.2")

# Serve frontend static files
BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDF_DIR = BASE_DIR / "pdfs"
PDF_DIR.mkdir(exist_ok=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


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


class SendPlanRequest(BaseModel):
    email: str
    plan_id: str
    bios: Optional[list] = None
    bio_platform: Optional[str] = "instagram"


@app.post("/api/send-plan")
async def send_plan_route(request: SendPlanRequest):
    """Fetch plan from Supabase and email it to the user."""
    email_addr = request.email.strip()
    if "@" not in email_addr:
        raise HTTPException(status_code=400, detail="Invalid email")

    plan = get_plan(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    artist_name = request.plan_id
    if plan.get("artist"):
        artist_name = plan["artist"].get("stage_name", request.plan_id)

    sent = send_strategy_email(
        to_email=email_addr,
        artist_name=artist_name,
        plan_data=plan.get("plan", {}),
        bios=request.bios,
        bio_platform=request.bio_platform or "instagram",
    )
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email")

    # Save to waitlist too
    try:
        supabase.table("waitlist").upsert(
            {"email": email_addr},
            on_conflict="email",
        ).execute()
    except Exception as e:
        print(f"Waitlist save error: {e}")

    return JSONResponse({"ok": True, "message": "Strategy sent!"})


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

    # Upload PDF to Supabase Storage
    pdf_url = None
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            with open(pdf_path, "rb") as f:
                supabase.storage.from_("pdfs").upload(
                    f"{plan_id}.pdf", f,
                    file_options={"content-type": "application/pdf"}
                )
            pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/pdfs/{plan_id}.pdf"
            update_plan_pdf_url(plan_id, pdf_url)
        except Exception as e:
            # Log but don't fail — still serve the file locally
            print(f"PDF upload failed: {e}")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{artist_name}-SiriusPulse-Strategy.pdf",
    )


@app.get("/strategy")
async def strategy_page():
    return FileResponse(FRONTEND_DIR / "strategy.html")


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/audit")
async def audit_page():
    return FileResponse(FRONTEND_DIR / "audit.html")


@app.get("/bio")
async def bio_page():
    return FileResponse(FRONTEND_DIR / "bio.html")


class BioRequest(BaseModel):
    stage_name: str
    genre: str
    subgenre: Optional[str] = ""
    career_stage: str
    vibes: list[str] = []
    about: Optional[str] = ""
    platform: str = "instagram"


@app.post("/bio")
async def create_bio(request: BioRequest):
    try:
        bios = generate_bios(
            stage_name=request.stage_name,
            genre=request.genre,
            subgenre=request.subgenre,
            career_stage=request.career_stage,
            vibes=request.vibes,
            about=request.about,
            platform=request.platform,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse({"bios": bios})


@app.post("/audit")
async def create_audit(
    insta_files: list[UploadFile] = Form(None),
    tiktok_files: list[UploadFile] = Form(None),
    youtube_files: list[UploadFile] = Form(None),
    twitter_files: list[UploadFile] = Form(None),
):
    # Collect files by platform
    platform_files: dict[str, list[str]] = {}
    for platform, uploads in [
        ("instagram", insta_files or []),
        ("tiktok", tiktok_files or []),
        ("youtube", youtube_files or []),
        ("twitter", twitter_files or []),
    ]:
        paths = []
        for upload in uploads:
            if not upload.content_type or not upload.content_type.startswith("image/"):
                continue
            suffix = os.path.splitext(upload.filename or ".png")[1] or ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                content = await upload.read()
                f.write(content)
                f.flush()
                paths.append(f.name)
        if paths:
            platform_files[platform] = paths

    if not platform_files:
        raise HTTPException(status_code=400, detail="No valid images provided")

    try:
        audit_result = audit_profiles(platform_files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")
    finally:
        # Clean up temp files
        for paths in platform_files.values():
            for p in paths:
                try:
                    os.unlink(p)
                except Exception:
                    pass

    # Save to Supabase if configured
    audit_id = str(uuid.uuid4())[:8]
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            supabase.table("audits").insert({
                "id": audit_id,
                "audit_data": audit_result,
                "platforms": list(platform_files.keys()),
            }).execute()
        except Exception as e:
            print(f"Audit save failed: {e}")

    return JSONResponse({"audit_id": audit_id, **audit_result})


@app.post("/api/waitlist")
async def join_waitlist(request: dict):
    email = request.get("email", "").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            supabase.table("waitlist").insert({"email": email}).execute()
        except Exception as e:
            print(f"Waitlist save failed: {e}")
            # Fall through — still return success

    return JSONResponse({"ok": True, "message": "You're on the list."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
