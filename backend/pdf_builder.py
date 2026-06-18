"""PDF generator using ReportLab."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Brand colors
BRAND_BLACK = HexColor("#0A0A0A")
BRAND_BLUE = HexColor("#4F8EFF")
BRAND_GRAY = HexColor("#6B7280")
BRAND_LIGHT = HexColor("#F3F4F6")


def _to_text(val):
    """Recursively convert any value to a readable string."""
    if isinstance(val, str):
        return val
    elif isinstance(val, list):
        return "\n".join(_to_text(v) for v in val)
    elif isinstance(val, dict):
        return " | ".join(f"{k}: {_to_text(v)}" for k, v in val.items())
    else:
        return str(val)


def build_pdf(plan_data: dict, artist_name: str, output_path: str, bios: list = None):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=28,
        textColor=BRAND_BLACK,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    tagline_style = ParagraphStyle(
        "Tagline",
        parent=styles["Normal"],
        fontSize=11,
        textColor=BRAND_GRAY,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=BRAND_BLUE,
        spaceBefore=18,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=BRAND_BLACK,
        spaceAfter=6,
        leading=15,
    )
    platform_header_style = ParagraphStyle(
        "PlatformHeader",
        parent=styles["Heading3"],
        fontSize=12,
        textColor=BRAND_BLACK,
        spaceBefore=14,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=BRAND_GRAY,
        spaceBefore=6,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )

    story = []

    # Header
    story.append(Paragraph("SIRIUS PULSE", ParagraphStyle("Logo", parent=title_style, fontSize=16, textColor=BRAND_BLUE)))
    story.append(Paragraph(artist_name, title_style))
    story.append(Paragraph("Content Strategy Plan", tagline_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=16))

    # Profile Audit
    story.append(Paragraph("Profile Audit", section_style))
    story.append(Paragraph(plan_data.get("profile_audit", ""), body_style))

    # Platforms
    platforms = plan_data.get("platforms", {})
    for platform, data in platforms.items():
        if not data:
            continue
        story.append(Paragraph(platform.capitalize(), section_style))

        # Content types
        story.append(Paragraph("Content Types", label_style))
        content_types = data.get("content_types", [])
        if content_types:
            story.append(Paragraph("• " + " • ".join(content_types), body_style))

        # Frequency + times
        freq = data.get("posting_frequency", "")
        times = data.get("best_times", "")
        if freq:
            story.append(Paragraph(f"<b>Frequency:</b> {freq}", body_style))
        if times:
            story.append(Paragraph(f"<b>Best Times:</b> {times}", body_style))

        # Example posts
        example_posts = data.get("example_posts", [])
        for i, post in enumerate(example_posts, 1):
            if isinstance(post, dict):
                story.append(Paragraph(f"<b>Example Post {i}:</b>", label_style))
                story.append(Paragraph(f"Hook: {post.get('hook','')}", body_style))
                story.append(Paragraph(f"Format: {post.get('format','')}", body_style))
                story.append(Paragraph(f"Caption: {post.get('caption_hint','')}", body_style))

    story.append(Spacer(1, 0.1 * inch))

    # Caption Framework
    caption = plan_data.get("caption_framework", "")
    if caption:
        story.append(Paragraph("Caption Framework", section_style))
        caption_text = _to_text(caption)
        story.append(Paragraph(caption_text.replace("\n", "<br/>"), body_style))

    # 30-day calendar
    calendar = plan_data.get("calendar_30day", "")
    if calendar:
        story.append(Paragraph("30-Day Content Calendar", section_style))
        calendar_text = _to_text(calendar)
        story.append(Paragraph(calendar_text.replace("\n", "<br/>"), body_style))

    # Growth tactics
    tactics = plan_data.get("growth_tactics", "")
    if tactics:
        story.append(Paragraph("Growth Tactics", section_style))
        tactics_text = _to_text(tactics)
        story.append(Paragraph(tactics_text.replace("\n", "<br/>"), body_style))

    # Bio section — only if bios were provided
    if bios:
        story.append(Paragraph("Artist Bio", section_style))
        for i, bio in enumerate(bios, 1):
            bio_text = _to_text(bio)
            story.append(Paragraph(f"<b>Bio {i}:</b>", label_style))
            story.append(Paragraph(bio_text.replace("\n", "<br/>"), body_style))
            story.append(Spacer(1, 0.05 * inch))

    # Footer
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_LIGHT, spaceAfter=8))
    story.append(Paragraph(
        "Generated by Sirius Pulse — Your artist's strategy, generated.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=BRAND_GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path
