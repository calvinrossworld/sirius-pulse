"""Hashtag generator using AI."""
import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are a world-class social media strategist specializing in music artists. You generate optimized, platform-specific hashtags that actually get discovered."""

USER_PROMPT_TEMPLATE = """Generate hashtags for a music artist. Return ONLY valid JSON — no markdown, no explanation.

Artist: {stage_name}
Genre: {genre}
Sub-genre/Style: {subgenre}
Promoting: {promoting}
Platforms: {platforms}

Return this exact JSON structure:
{{
  "hashtags": {{
    "instagram": {{
      "Genre Tags": ["#genre #genreartist etc — broad discovery"],
      "Niche Tags": ["#mood #vibe #aesthetic — targeted to their specific style"],
      "Trending Tags": ["currently popular music hashtags in their lane"],
      "Artist Tags": ["#{stage_name} or variations they own"],
      "Campaign Tags": ["#{promotion_name} or relevant campaign tags"]
    }},
    "tiktok": {{ ... same structure ... }},
    "youtube": {{ ... same structure ... }},
    "twitter": {{ ... same structure ... }}
  }}
}}

Rules:
- 8-12 hashtags per category per platform
- Mix of follower sizes: some huge (#100k+ posts), some mid, some small niche
- Never suggest hashtags with millions of posts that are completely dominated by established artists
- Include 1-2 ultra-specific niche tags that have low competition
- Hashtags must be relevant to {genre} and {subgenre}
- Return valid JSON only"""


def generate_hashtags(genre: str, subgenre: str, promoting: str, stage_name: str, platforms: list[str]) -> dict:
    user_prompt = USER_PROMPT_TEMPLATE.format(
        stage_name=stage_name or "their name",
        genre=genre,
        subgenre=subgenre or "not specified",
        promoting=promoting,
        platforms=", ".join(platforms),
    )

    response = client.chat.completions.create(
        model="google/gemini-2.5-pro",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=2048,
        temperature=0.8,
        extra_body={"thinking": {"type": "disabled"}},
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
