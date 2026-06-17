"""Hashtag generator using AI."""
import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are an expert music social media strategist. Generate optimized hashtags for artists."""


def generate_hashtags(genre: str, subgenre: str, promoting: str, stage_name: str, platforms: list[str]) -> dict:
    """Generate hashtags for requested platforms. Returns {hashtags: {platform: [list of hashtags]}}."""
    import urllib.request

    platforms_str = ", ".join(platforms)
    prompt = f"""Generate 20 hashtags for a {genre} artist ({subgenre or 'general'}). They are promoting: {promoting}

Return ONLY valid JSON like this: {{"hashtags": {{"instagram": ["#tag1", "#tag2", ...], "tiktok": ["#tag1", ...]}}}}
- Exactly 20 hashtags per platform listed
- Mix of broad (high posts), medium, and niche (low competition) hashtags
- Relevant to {genre} and {subgenre}
- Only include the platforms: {platforms_str}
- Return JSON only, no markdown, no explanation"""

    from openai import OpenAI
    c = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY", ""), base_url="https://openrouter.ai/api/v1")
    resp = c.chat.completions.create(
        model="openrouter/deepseek/deepseek-v4-pro",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        temperature=0.7,
    )

    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
        # Normalize to flat lists if model returned nested categories
        normalized = {}
        for platform in platforms:
            if platform in result.get("hashtags", {}):
                val = result["hashtags"][platform]
                if isinstance(val, dict):
                    # Flatten all category values into one list
                    tags = []
                    for cat_tags in val.values():
                        if isinstance(cat_tags, list):
                            tags.extend(cat_tags)
                    normalized[platform] = tags[:20]
                elif isinstance(val, list):
                    normalized[platform] = val[:20]
                else:
                    normalized[platform] = []
            else:
                normalized[platform] = []
        return {"hashtags": normalized}
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON from model: {raw[:300]}")
