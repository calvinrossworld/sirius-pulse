"""Artist bio generator using AI — EPK style, always included in strategy PDF."""
import os
import json
import re

_client_cache = None


def _get_client():
    global _client_cache
    if _client_cache is None:
        from openai import OpenAI
        _client_cache = OpenAI(
            api_key=os.environ.get("OPENROUTER_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
        )
    return _client_cache


SYSTEM_PROMPT = """You are a world-class music publicist and brand writer. You write tight, compelling artist bios that sound authentic and capture a specific sonic identity. You specialize in R&B, hip-hop, pop, and Afrobeats."""


def generate_bios(
    stage_name: str,
    genre: str,
    subgenre: str,
    career_stage: str,
    vibes: list,
    about: str,
    research_data: dict = None,
) -> list[str]:
    """Generate 3 EPK-style artist bios. Always returns 3 variants."""
    research = research_data or {}

    user_prompt = f"""Write a 2-3 sentence artist bio for a press kit / EPK. Return ONLY valid JSON array of 3 bio strings — no markdown, no explanation.

Artist: {stage_name}
Genre: {genre}
Sub-genre/Style: {subgenre or 'not specified'}
Career Stage: {career_stage}
Vibe: {vibes or 'confident, authentic'}
About: {about or 'not specified'}

Research context (factor into bios if helpful):
- Artist's existing presence: {research.get('artist_profile', 'Limited information — artist is building their presence.')}

Rules:
- Exactly 3 different bios, each 2-3 sentences
- Third-person voice (written about the artist, not by them)
- Cover: who they are, what they sound like, why it matters
- Vary tone across the 3 options (e.g., one confident/assertive, one storytelling, one evocative)
- Return: ["bio 1", "bio 2", "bio 3"]"""

    client = _get_client()
    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=2048,
        temperature=0.85,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code blocks
    if raw.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()

    # Try direct parse
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed[:3]
    except json.JSONDecodeError:
        pass

    # Try extracting array from raw text
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return parsed[:3]
        except Exception:
            pass

    # Fallback: split by double newlines or numbered items
    lines = [l.strip() for l in raw.replace('"', '').split('\n') if l.strip() and len(l.strip()) > 20]
    if lines:
        return lines[:3]

    raise ValueError(f"Bio generation failed. Raw output: {raw[:300]}")
