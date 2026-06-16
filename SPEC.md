# Sirius Pulse — Product Specification

## What It Is

Sirius Pulse is an AI-powered content strategy generator for emerging music artists. An artist fills out a short intake form, and the app generates a personalized multi-platform content strategy — delivered as a clean in-app plan and a downloadable PDF.

## Brand

- **Name:** Sirius Pulse
- **Tagline:** "Your artist's strategy, generated."
- **Vibe:** Dark, premium, confident — like a record label meets a Bloomberg terminal
- **Color:** Deep black background, white text, electric blue accents (#4F8EFF)
- **Font:** Inter (clean, modern, readable)

## How It Works

1. Artist fills out an intake form (3–4 minutes)
2. AI generates a full content strategy tailored to their genre, style, and goals
3. Plan appears on screen + can be downloaded as a PDF

## Intake Form Fields

| Field | Type | Notes |
|---|---|---|
| Stage name | text | required |
| Genre | dropdown | R&B / Hip-Hop / Pop / Afrobeats / Other |
| Sub-genre / style | text | optional — e.g., "dark R&B, moody vibes" |
| Career stage | dropdown | Just starting / Some traction / Ready to scale |
| Platforms | multi-select | Instagram / TikTok / YouTube / Twitter/X / All |
| Currently promoting | dropdown | Single / Album / Tour / Brand deal / Nothing specific |
| Artists to model | text | optional — "like Drake, SZA..." |
| Biggest challenge | textarea | optional |

## Output: The Plan

The AI generates a strategy with these sections:

### 1. Profile Audit
- 3–4 sentence assessment of how they'd appear to a new fan landing on their page today

### 2. Content Strategy by Platform
For each selected platform:
- **Content types to focus on** (Reels, carousels, lives, etc.)
- **Posting frequency** (posts per week)
- **Best posting windows**
- **2 example post ideas** with hook + format

### 3. Caption Framework
- 2–3 caption templates they can reuse
- Tone guide (witty / vulnerable / direct / etc.)

### 4. 30-Day Content Calendar
- Week-by-week breakdown of what to post
- Content mix ratio (e.g., 40% Reels, 30% carousels, 30% lives)

### 5. Growth Tactics
- 3 specific, actionable things to try in the next 7 days
- What to avoid

## Technical Stack

- **Backend:** Python FastAPI
- **Frontend:** Vanilla HTML/CSS/JS (single page, no framework needed)
- **AI:** Gemini 2.5 Pro via OpenRouter API
- **PDF:** ReportLab (Python server-side)
- **Hosting:** Local run for now; deployable to Render or Railway

## API Design

### `POST /generate`
**Request body:**
```json
{
  "stage_name": "string",
  "genre": "string",
  "subgenre": "string",
  "career_stage": "string",
  "platforms": ["string"],
  "promoting": "string",
  "model_artists": "string",
  "challenge": "string"
}
```

**Response:**
```json
{
  "plan": {
    "profile_audit": "string",
    "platforms": { ... },
    "caption_framework": "string",
    "calendar_30day": "string",
    "growth_tactics": "string"
  },
  "plan_id": "string"
}
```

### `GET /plan/<plan_id>`
Returns the stored plan JSON.

### `GET /download/<plan_id>`
Returns the plan as a formatted PDF download.

## File Structure

```
sirius-pulse/
├── SPEC.md
├── backend/
│   ├── main.py          # FastAPI app
│   ├── generator.py     # AI prompt construction + call
│   ├── pdf_builder.py   # ReportLab PDF generation
│   ├── storage.py       # Simple JSON file storage
│   └── requirements.txt
└── frontend/
    ├── index.html       # Main app page
    ├── style.css
    └── app.js
```

## Status

- [x] SPEC.md written
- [ ] Backend built
- [ ] Frontend built
- [ ] AI wired up
- [ ] PDF download working
- [ ] End-to-end tested