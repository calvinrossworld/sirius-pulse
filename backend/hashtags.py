"""Hashtag generator using AI."""
import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are a world-class social media strategist specializing in music artists. You generate optimized, platform-specific hashtags that actually get discovered."""

USER_PROMPT_TEMPLATE = """Generate hashtags for a music artist. You MUST return ONLY valid JSON — no markdown, no code blocks, no explanation. Just a raw JSON object.

Artist: {stage_name}
Genre: {genre}
Sub-genre/Style: {subgenre}
Promoting: {promoting}
Platforms: {platforms}

Output format — fill in ALL sections for ALL platforms listed:
{{
  "hashtags": {{
    "instagram": {{
      "Genre Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Niche Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Trending Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Artist Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Campaign Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
    }},
    "tiktok": {{
      "Genre Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Niche Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Trending Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Artist Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Campaign Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
    }},
    "youtube": {{
      "Genre Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Niche Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Trending Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Artist Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Campaign Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
    }},
    "twitter": {{
      "Genre Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Niche Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Trending Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Artist Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
      "Campaign Tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
    }}
  }}
}}

Rules:
- Exactly 6 hashtags per category per platform — no more, no less
- All strings in double quotes
- No trailing commas
- No None, null, or undefined values — use empty arrays [] if needed
- Mix of follower sizes: some huge broad hashtags, some mid, some ultra-specific niche (low competition)
- Hashtags must be directly relevant to {genre} and {subgenre}
- Only include platforms from the list above"""


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
        max_tokens=4096,
        temperature=0.8,
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
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Try to fix common issues
        raw = raw.replace("'", '"')
        raw = raw.replace(",}", "}")
        raw = raw.replace(",]", "]")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"AI returned invalid JSON: {raw[:200]}")
