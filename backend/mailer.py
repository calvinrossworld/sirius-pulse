"""Email template builder and sender via Mailgun API."""
import os
import httpx


def build_strategy_email(artist_name: str, plan_data: dict, bios: list = None, bio_platform: str = "instagram") -> dict:
    """Build a branded HTML email with the full strategy content."""
    platforms = plan_data.get("platforms", {})
    profile_audit = plan_data.get("profile_audit", "")
    caption_framework = plan_data.get("caption_framework", "")
    calendar = plan_data.get("calendar_30day", "")
    growth_tactics = plan_data.get("growth_tactics", "")

    def section(title, content):
        if not content:
            return ""
        return f"""
        <div style="margin-bottom:36px">
          <div style="font-size:11px;font-weight:700;color:#4F8EFF;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px">{title}</div>
          <div style="color:#D1D5DB;font-size:15px;line-height:1.7">{content}</div>
        </div>"""

    def platform_block(name, icon, data):
        if not data:
            return ""
        content_types = ", ".join(data.get("content_types", []))
        freq = data.get("posting_frequency", "")
        times = data.get("best_times", "")
        examples = data.get("example_posts", [])

        ex_items = []
        for ex in examples[:3]:
            hook = ex.get("hook", "")
            fmt = ex.get("format", "")
            caption = ex.get("caption_hint", "")
            ex_items.append(f'<li style="margin-bottom:12px"><strong style="color:#fff">{icon} {fmt}</strong><br><span style="color:#9CA3AF">{hook}</span><br><span style="color:#6B7280;font-size:13px">Caption: {caption}</span></li>')

        examples_html = f"<ul style='list-style:none;padding:0;margin:0'>{''.join(ex_items)}</ul>" if ex_items else ""

        return f"""
        <div style="margin-bottom:32px">
          <div style="font-size:18px;font-weight:800;color:#fff;margin-bottom:14px">{icon} {name}</div>
          <div style="margin-bottom:8px"><span style="color:#6B7280;font-size:13px">CONTENT TYPES: </span><span style="color:#fff">{content_types}</span></div>
          <div style="margin-bottom:8px"><span style="color:#6B7280;font-size:13px">FREQUENCY: </span><span style="color:#fff">{freq}</span></div>
          <div style="margin-bottom:16px"><span style="color:#6B7280;font-size:13px">BEST TIMES: </span><span style="color:#fff">{times}</span></div>
          {examples_html}
        </div>"""

    platform_sections = ""
    platform_icons = {"instagram": "📸", "tiktok": "🎵", "youtube": "▶️", "twitter": "🐦"}
    for pname, pdata in platforms.items():
        icon = platform_icons.get(pname, "•")
        platform_sections += platform_block(pname.capitalize(), icon, pdata)

    bios_html = ""
    if bios:
        bio_label = {"instagram": "Instagram", "tiktok": "TikTok", "epk": "EPK"}.get(bio_platform, "Artist")
        bios_content = "<br><br>".join([
            f"<div style='margin-bottom:16px;border-left:3px solid #4F8EFF;padding-left:16px;color:#D1D5DB;font-size:15px;line-height:1.7'>{b.get('text', b)}</div>"
            for b in bios[:3]
        ])
        bios_html = f"""
        <div style="margin-bottom:36px">
          <div style="font-size:11px;font-weight:700;color:#22C55E;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px">Your {bio_label} Bios</div>
          {bios_content}
        </div>"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Your Sirius Pulse Strategy</title>
</head>
<body style="margin:0;padding:0;background:#0A0A0A;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif">
  <div style="max-width:600px;margin:0 auto;padding:40px 24px">
    <div style="margin-bottom:40px">
      <div style="font-size:13px;font-weight:800;letter-spacing:3px;color:#4F8EFF;margin-bottom:8px">SIRIUS PULSE</div>
      <h1 style="font-size:28px;font-weight:900;color:#fff;margin:0 0 8px">Your Content Strategy</h1>
      <p style="color:#6B7280;font-size:15px;margin:0">Prepared for {artist_name}</p>
    </div>
    <div style="height:1px;background:#1F2937;margin:32px 0"></div>
    {section("Profile Audit", profile_audit)}
    {section("Platform Strategy", platform_sections)}
    {section("Caption Framework", caption_framework)}
    {section("30-Day Content Calendar", calendar)}
    {section("Growth Tactics", growth_tactics)}
    {bios_html}
    <div style="height:1px;background:#1F2937;margin:32px 0"></div>
    <div style="color:#374151;font-size:11px;text-align:center">
      Built with Sirius Pulse · Free AI tools for independent artists
    </div>
  </div>
</body>
</html>"""

    subject = f"Your Sirius Pulse Strategy — {artist_name}"
    return {"subject": subject, "html": html}


def send_strategy_email(to_email: str, artist_name: str, plan_data: dict, bios: list = None, bio_platform: str = "instagram") -> bool:
    """Send the strategy email via Mailgun API."""
    api_key = os.environ.get("MAILGUN_API_KEY", "")
    domain = os.environ.get("MAILGUN_DOMAIN", "")

    if not api_key or not domain:
        print("MAILGUN_API_KEY or MAILGUN_DOMAIN not set")
        return False

    email = build_strategy_email(artist_name, plan_data, bios, bio_platform)

    try:
        response = httpx.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"Sirius Pulse <mailgun@{domain}>",
                "to": to_email,
                "subject": email["subject"],
                "html": email["html"],
            },
            timeout=15.0,
        )
        if response.status_code >= 400:
            print(f"Mailgun error: {response.status_code} {response.text}")
            return False
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False
