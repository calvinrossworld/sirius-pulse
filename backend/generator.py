"""AI strategy generator using OpenAI client with OpenRouter."""
import os
import json
import re
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_KEY", ""),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are a strategic content advisor for independent and emerging musicians. Your specialty is R&B, hip-hop, pop, and Afrobeats. You understand how each platform's algorithm works in 2025, what content actually converts followers to fans, and what separates artists who stagnate from those who build real momentum.

For every artist, you assess their current profile, identify the single highest-leverage move they can make this week, and build a sustainable content system around it.

You return strategy plans as clean JSON. Every piece of advice should be specific enough that the artist could act on it immediately — not "post more Reels" but "post a 15-second hook reveal Reel at 7pm on Thursday showing your recording setup, with the caption starting with the hook lyrics."

Per platform, include: what to post, why it works for their genre and career stage, when to post, and what the algorithm is rewarding right now for their specific type of content.

Flag one common mistake artists at their career stage make on each platform, and how to avoid it."""

USER_PROMPT_TEMPLATE = """Generate a personalized content strategy for the following artist. Return ONLY valid JSON — no markdown, no explanation.

Artist details:
- Stage name: {stage_name}
- Genre: {genre}
- Sub-genre / style: {subgenre}
- Career stage: {career_stage}
- Platforms to focus on: {platforms}
- Currently promoting: {promoting}
- Artists to model after: {model_artists}
- Biggest challenge: {challenge}
- Current year: 2025

Research findings:
- Artist landscape: {artist_profile}
- Genre context: {genre_trends}
- What's working in their lane: {model_context}

Return this exact JSON structure:
{{
  "profile_audit": "3-4 sentence assessment of how their page looks to a new fan today",
  "quick_win": "the single highest-leverage action to take in the next 48 hours — be extremely specific",
  "platforms": {{
    "instagram": {{
      "content_types": ["list of 3-4 content types specific to their genre and career stage"],
      "posting_frequency": "posts per week",
      "best_times": "best posting windows",
      "common_mistake": "one thing artists at their career stage commonly get wrong on this platform",
      "example_posts": [
        {{"hook": "specific hook tied to their actual music, story, or current project", "format": "Reel/Carousel/Post/etc", "caption_hint": "caption direction"}},
        {{"hook": "specific hook tied to their actual music, story, or current project", "format": "Reel/Carousel/Post/etc", "caption_hint": "caption direction"}}
      ]
    }},
    "tiktok": {{
      "content_types": ["list of 3-4 content types specific to their genre"],
      "posting_frequency": "posts per week",
      "best_times": "best posting windows",
      "common_mistake": "one thing artists at their career stage commonly get wrong on this platform",
      "example_posts": [
        {{"hook": "specific hook tied to their actual music or story", "format": "TikTok video type", "caption_hint": "caption direction"}},
        {{"hook": "specific hook tied to their actual music or story", "format": "TikTok video type", "caption_hint": "caption direction"}}
      ]
    }},
    "youtube": {{
      "content_types": ["list of 3-4 content types"],
      "posting_frequency": "posts per week",
      "best_times": "best posting windows",
      "common_mistake": "one thing artists at their career stage commonly get wrong on this platform",
      "example_posts": [
        {{"hook": "specific hook idea", "format": "Shorts/Long-form/etc", "caption_hint": "description direction"}},
        {{"hook": "specific hook idea", "format": "Shorts/Long-form/etc", "caption_hint": "description direction"}}
      ]
    }},
    "twitter": {{
      "content_types": ["list of 3-4 content types"],
      "posting_frequency": "posts per week",
      "best_times": "best posting windows",
      "common_mistake": "one thing artists at their career stage commonly get wrong on this platform",
      "example_posts": [
        {{"hook": "specific hook idea", "format": "text/thread/media", "caption_hint": "text direction"}},
        {{"hook": "specific hook idea", "format": "text/thread/media", "caption_hint": "text direction"}}
      ]
    }}
  }},
  "caption_framework": "2-3 caption templates with tone guidance",
  "calendar_30day": "Week 1 focus: this week's specific priority actions; Weeks 2-4: broader content direction and milestones",
  "growth_tactics": "3 specific actions to take in next 7 days + 2 things to avoid"
}}

Only include platforms from the user's selected list above. If 'all' was selected, include all four platforms."""


def _parse_json(raw: str) -> dict | None:
    """Attempt to parse JSON from model output, handling various formats."""
    raw = raw.strip()
    if raw.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        return None


def generate_plan(artist_data: dict, research_data: dict = None, max_retries: int = 2) -> dict:
    platforms_str = ", ".join(artist_data.get("platforms", []))
    research = research_data or {}

    user_prompt = USER_PROMPT_TEMPLATE.format(
        stage_name=artist_data.get("stage_name", ""),
        genre=artist_data.get("genre", ""),
        subgenre=artist_data.get("subgenre", "not specified"),
        career_stage=artist_data.get("career_stage", ""),
        platforms=platforms_str,
        promoting=artist_data.get("promoting", "nothing specific"),
        model_artists=artist_data.get("model_artists", "none specified"),
        challenge=artist_data.get("challenge", "none specified"),
        artist_profile=research.get("artist_profile", "Limited information found about this artist."),
        genre_trends=research.get("genre_trends", "Focus on authentic, genre-specific content."),
        model_context=research.get("model_artist_context", "No model artist context available."),
    )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=6144,
                temperature=0.8,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content.strip()
            result = _parse_json(raw)

            if result is None:
                raise ValueError(f"Could not parse JSON from response: {raw[:200]}")

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

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue

    raise ValueError(f"Plan generation failed after {max_retries + 1} attempts: {last_error}")
