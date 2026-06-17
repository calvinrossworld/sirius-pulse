"""AI profile auditor using GPT-4o vision via OpenRouter."""
import os
import json
import base64
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are an expert social media strategist who has audited hundreds of artist profiles across Instagram, TikTok, YouTube, and Twitter/X. You give blunt, specific, actionable feedback.

You will receive screenshots of an artist's social profiles. Analyze each one and return a structured JSON audit.

For each platform provided, assess:
- Profile photo / visual branding consistency
- Bio clarity (who they are, what they do, why follow)
- Content aesthetic and grid cohesion
- Bio link usage
- Highlights/Reels tab quality (if visible)
- Posting consistency signals
- Any red flags or missed opportunities

Return a JSON object with this exact structure:
{
  "grade": "A" | "B" | "C" | "D" | "F",
  "overall_summary": "2-3 sentence overall assessment of their presence",
  "platform_audits": {
    "instagram": {
      "grade": "A|B|C|D|F",
      "overall_summary": "2-3 sentences",
      "strengths": ["strength 1", "strength 2"],
      "weaknesses": ["weakness 1", "weakness 2"],
      "specific_fixes": ["specific actionable fix 1", "specific actionable fix 2"]
    },
    "tiktok": { ... same structure ... },
    "youtube": { ... same structure ... },
    "twitter": { ... same structure ... }
  },
  "top_actions": [
    "Highest priority thing to fix or add — be specific",
    "Second priority — specific and actionable",
    "Third priority — specific and actionable"
  ]
}

Only include platforms where screenshots were provided. Return valid JSON only — no markdown, no explanation."""

USER_PROMPT = """Analyze the provided social media profile screenshots for this artist. Provide a thorough, honest audit with specific actionable feedback.

Screenshots provided: {platforms_list}

Return the structured JSON audit now."""


def encode_image(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def audit_profiles(image_files: dict[str, list[str]]) -> dict:
    """
    image_files: { "instagram": ["/tmp/path1.png", ...], "tiktok": [...], ... }
    Returns parsed audit dict.
    """
    if not image_files:
        raise ValueError("No images provided")

    platforms_provided = [p for p, imgs in image_files.items() if imgs]
    platforms_list = ", ".join(platforms_provided)

    # Build content blocks for the vision model
    content = [{"type": "text", "text": USER_PROMPT.format(platforms_list=platforms_list)}]

    for platform, paths in image_files.items():
        if not paths:
            continue
        for path in paths:
            try:
                b64 = encode_image(path)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })
            except Exception:
                continue

    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        max_tokens=4096,
        temperature=0.5,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
