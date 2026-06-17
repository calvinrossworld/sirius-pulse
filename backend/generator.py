"""AI strategy generator using OpenAI client with OpenRouter."""
import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are a world-class music marketing strategist who has worked with emerging and major artists across R&B, hip-hop, pop, and Afrobeats. You write plans that are specific, actionable, and tailored to each artist's unique voice and career stage.

You generate content strategy plans in clean JSON format. Be specific — no generic advice."""

USER_PROMPT_TEMPLATE = """Generate a personalized content strategy for the following artist. Return ONLY valid JSON — no markdown, no explanation, just the JSON object.

Artist details:
- Stage name: {stage_name}
- Genre: {genre}
- Sub-genre / style: {subgenre}
- Career stage: {career_stage}
- Platforms to focus on: {platforms}
- Currently promoting: {promoting}
- Artists to model after (optional): {model_artists}
- Biggest challenge (optional): {challenge}

Return this exact JSON structure:
{{
  "profile_audit": "3-4 sentence assessment of how their page looks to a new fan today",
  "platforms": {{
    "instagram": {{
      "content_types": ["list of 3-4 content types"],
      "posting_frequency": "posts per week",
      "best_times": "best posting windows",
      "example_posts": [
        {{"hook": "specific hook idea", "format": "Reel/Carousel/Post/etc", "caption_hint": "caption direction"}},
        {{"hook": "specific hook idea", "format": "Reel/Carousel/Post/etc", "caption_hint": "caption direction"}}
      ]
    }},
    "tiktok": {{ ... same structure ... }},
    "youtube": {{ ... same structure ... }},
    "twitter": {{ ... same structure ... }}
  }},
  "caption_framework": "2-3 caption templates with tone guidance",
  "calendar_30day": "week-by-week 30-day content calendar overview",
  "growth_tactics": "3 specific actions to take in next 7 days + 2 things to avoid"
}}

Only include platforms from the list above. If 'all' was selected, include all four platforms."""


def generate_plan(artist_data: dict) -> dict:
    platforms_str = ", ".join(artist_data.get("platforms", []))
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        stage_name=artist_data.get("stage_name", ""),
        genre=artist_data.get("genre", ""),
        subgenre=artist_data.get("subgenre", "not specified"),
        career_stage=artist_data.get("career_stage", ""),
        platforms=platforms_str,
        promoting=artist_data.get("promoting", "nothing specific"),
        model_artists=artist_data.get("model_artists", "none specified"),
        challenge=artist_data.get("challenge", "none specified"),
    )

    response = client.chat.completions.create(
        model="google/gemini-2.5-pro",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=6144,
        temperature=0.8,
        response_format={"type": "json_object"},
        extra_body={"thinking": {"type": "disabled"}},
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)

    # Normalize growth_tactics to string if model returned an object
    gt = result.get("growth_tactics")
    if isinstance(gt, dict):
        parts = []
        if gt.get("next_7_days_actions"):
            parts.append("Next 7 days: " + ". ".join(gt["next_7_days_actions"]))
        if gt.get("things_to_avoid"):
            parts.append("Avoid: " + ". ".join(gt["things_to_avoid"]))
        result["growth_tactics"] = " | ".join(parts)

    return result