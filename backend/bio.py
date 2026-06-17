"""Artist bio generator using AI."""
import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.env…EY", ""),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are a world-class music publicist and brand writer. You write tight, compelling artist bios that sound authentic and capture a specific sonic identity."""

USER_PROMPT_TEMPLATES = {
    "instagram": """Write a professional Instagram artist bio for a music artist. Return ONLY valid JSON array of 3 bio strings — no markdown, no explanation.

Artist: {stage_name}
Genre: {genre}
Sub-genre/Style: {subgenre}
Career Stage: {career_stage}
Vibe: {vibes}
About: {about}

Rules:
- Exactly 3 different bios, each hitting the character limit of 150 chars or under
- Each bio must be in the JSON array as separate strings
- Vary the approach: one confident/assertive, one storytelling/focused on the music, one more mysterious or evocative
- Include genre signals where they fit naturally
- No emojis, no line breaks, no special characters
- All bios must be DIFFERENT from each other in tone/angle
- Return: ["bio 1", "bio 2", "bio 3"]""",

    "tiktok": """Write a tight TikTok artist bio. Return ONLY valid JSON array of 3 bio strings — no markdown, no explanation.

Artist: {stage_name}
Genre: {genre}
Career Stage: {career_stage}
Vibe: {vibes}
About: {about}

Rules:
- Exactly 3 different bios, each 80 chars or under
- TikTok bios are ultra-short — make every character count
- Vary the angle: one confident, one more intriguing/mysterious, one focused on what makes them different
- No emojis
- Return: ["bio 1", "bio 2", "bio 3"]""",

    "epk": """Write a 2-3 sentence artist bio for a press kit / EPK. Return ONLY valid JSON array of 3 bio strings — no markdown, no explanation.

Artist: {stage_name}
Genre: {genre}
Sub-genre/Style: {subgenre}
Career Stage: {career_stage}
Vibe: {vibes}
About: {about}

Rules:
- Exactly 3 different bios, each 2-3 sentences
- Third-person voice (written about the artist, not by them)
- Cover: who they are, what they sound like, why it matters
- Vary tone across the 3 options
- Return: ["bio 1", "bio 2", "bio 3"]""",
}


def generate_bios(stage_name: str, genre: str, subgenre: str, career_stage: str,
                   vibes: list, about: str, platform: str) -> list[str]:
    template = USER_PROMPT_TEMPLATES.get(platform, USER_PROMPT_TEMPLATES["instagram"])
    vibes_str = ", ".join(vibes) if vibes else "confident, authentic"

    user_prompt = template.format(
        stage_name=stage_name,
        genre=genre,
        subgenre=subgenre or "not specified",
        career_stage=career_stage,
        vibes=vibes_str,
        about=about or "not specified",
    )

    response = client.chat.completions.create(
        model="google/gemini-2.5-pro",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.85,
        response_format={"type": "json_object"},
        extra_body={"thinking": {"type": "disabled"}},
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except json.JSONDecodeError:
        # Try to extract array
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        raise ValueError(f"Could not parse bio response: {raw[:200]}")
