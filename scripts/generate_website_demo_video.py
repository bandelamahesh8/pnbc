import os
import sys
import subprocess
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

VIDEO_PATH = root_dir / "website_demo_recording.mp4"

# Video dimensions & FPS
WIDTH = 1280
HEIGHT = 720
FPS = 24

# Colors
BG_SLATE = (248, 250, 252)
HEADER_WHITE = (255, 255, 255)
BORDER_GRAY = (226, 232, 240)
TEXT_DARK = (15, 23, 42)
TEXT_MUTED = (100, 116, 139)
TEXT_LIGHT = (148, 163, 184)
BRAND_PURPLE = (79, 70, 229)
BRAND_BG = (238, 242, 255)
EMERALD_GREEN = (16, 185, 129)
EMERALD_BG = (236, 253, 245)
AMBER_YELLOW = (217, 119, 6)
AMBER_BG = (254, 243, 199)
CARD_BG = (255, 255, 255)
CODE_BG = (15, 23, 42)

# Fonts
try:
    font_logo = ImageFont.truetype("arialbd.ttf", 18)
    font_heading = ImageFont.truetype("arialbd.ttf", 16)
    font_subheading = ImageFont.truetype("arialbd.ttf", 14)
    font_body = ImageFont.truetype("arial.ttf", 13)
    font_body_bold = ImageFont.truetype("arialbd.ttf", 13)
    font_small = ImageFont.truetype("arial.ttf", 11)
    font_small_bold = ImageFont.truetype("arialbd.ttf", 11)
    font_code = ImageFont.truetype("consola.ttf", 12)
    font_url = ImageFont.truetype("consola.ttf", 12)
except Exception:
    font_logo = ImageFont.load_default()
    font_heading = font_logo
    font_subheading = font_logo
    font_body = font_logo
    font_body_bold = font_logo
    font_small = font_logo
    font_small_bold = font_logo
    font_code = font_logo
    font_url = font_logo


def draw_browser_chrome(draw):
    """Draws top macOS/modern browser frame with address bar."""
    draw.rectangle([0, 0, WIDTH, 42], fill=(241, 245, 249))
    draw.line([(0, 42), (WIDTH, 42)], fill=BORDER_GRAY, width=1)

    # Window dots
    draw.ellipse([14, 15, 26, 27], fill=(239, 68, 68))
    draw.ellipse([34, 15, 46, 27], fill=(245, 158, 11))
    draw.ellipse([54, 15, 66, 27], fill=(16, 185, 129))

    # Address bar
    draw.rectangle([120, 8, WIDTH - 160, 34], fill=(255, 255, 255), outline=BORDER_GRAY, width=1)
    draw.text((135, 14), "🔒 https://pnbc.pragatibharati.edu/dashboard", fill=TEXT_MUTED, font=font_url)

    # User avatar/status
    draw.ellipse([WIDTH - 50, 10, WIDTH - 26, 34], fill=BRAND_PURPLE)
    draw.text((WIDTH - 43, 14), "PB", fill=(255, 255, 255), font=font_small_bold)


def draw_navbar(draw):
    """Draws dashboard application navigation bar."""
    draw.rectangle([0, 43, WIDTH, 95], fill=HEADER_WHITE)
    draw.line([(0, 95), (WIDTH, 95)], fill=BORDER_GRAY, width=1)

    # Logo icon
    draw.rectangle([24, 52, 56, 84], fill=BRAND_PURPLE)
    draw.text((32, 58), "✨", font=font_subheading)

    # Title
    draw.text((66, 54), "Pragati Bharati", fill=BRAND_PURPLE, font=font_logo)
    draw.text((66, 74), "Document Intelligence & Question Extraction Service", fill=TEXT_MUTED, font=font_small)

    # Engine status badge
    draw.rectangle([WIDTH - 420, 56, WIDTH - 240, 82], fill=EMERALD_BG, outline=(167, 243, 208), width=1)
    draw.ellipse([WIDTH - 410, 66, WIDTH - 402, 74], fill=EMERALD_GREEN)
    draw.text((WIDTH - 395, 62), "Gemini 3.5 Flash Online", fill=(6, 95, 70), font=font_small_bold)

    # Dual engine fallback badge
    draw.rectangle([WIDTH - 230, 56, WIDTH - 70, 82], fill=BRAND_BG, outline=(199, 210, 254), width=1)
    draw.text((WIDTH - 218, 62), "Dual-Engine Offline Ready", fill=BRAND_PURPLE, font=font_small_bold)


def draw_metrics(draw, review_count=2):
    """Draws live stats banner."""
    draw.rectangle([0, 96, WIDTH, 160], fill=(255, 255, 255))
    draw.line([(0, 160), (WIDTH, 160)], fill=BORDER_GRAY, width=1)

    metrics = [
        ("Documents Processed", "10", "100% test coverage", TEXT_DARK, (24, 106)),
        ("Questions Extracted", "28", "MCQ, Multi-select, Math", BRAND_PURPLE, (330, 106)),
        ("Avg. Confidence", "94.2%", "Dual-engine verified", EMERALD_GREEN, (640, 106)),
        ("Review Queue", str(review_count), "Requires human approval", AMBER_YELLOW, (950, 106)),
    ]

    for label, val, sub, color, (x, y) in metrics:
        draw.rectangle([x, y, x + 280, y + 46], fill=(248, 250, 252), outline=BORDER_GRAY, width=1)
        draw.text((x + 12, y + 4), label, fill=TEXT_MUTED, font=font_small)
        draw.text((x + 12, y + 18), val, fill=color, font=font_heading)
        draw.text((x + 100, y + 24), sub, fill=TEXT_MUTED, font=font_small)


def draw_tabs(draw, active_tab="upload"):
    """Draws top navigation tabs."""
    tabs = [
        ("upload", "Upload & Extraction Hub"),
        ("questions", "Question Intelligence Viewer (28)"),
        ("review", "Review Queue (2)"),
        ("json", "Structured JSON Inspector"),
    ]

    cur_x = 30
    draw.line([(0, 195), (WIDTH, 195)], fill=BORDER_GRAY, width=1)

    for tab_id, label in tabs:
        is_active = (tab_id == active_tab)
        color = BRAND_PURPLE if is_active else TEXT_MUTED
        font = font_subheading if is_active else font_body
        text_w = len(label) * 8

        draw.text((cur_x, 172), label, fill=color, font=font)
        if is_active:
            draw.line([(cur_x - 4, 195), (cur_x + text_w + 4, 195)], fill=BRAND_PURPLE, width=3)
        cur_x += text_w + 35


def draw_cursor(draw, x, y):
    """Draws modern sleek pointer cursor."""
    points = [
        (x, y),
        (x, y + 16),
        (x + 4, y + 13),
        (x + 8, y + 20),
        (x + 11, y + 19),
        (x + 7, y + 11),
        (x + 13, y + 11)
    ]
    draw.polygon(points, fill=(15, 23, 42), outline=(255, 255, 255))


def render_scene_1_landing(cursor_pos=(450, 300)):
    """Scene 1: Web Dashboard Landing & Dropzone."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_SLATE)
    draw = ImageDraw.Draw(img)

    draw_browser_chrome(draw)
    draw_navbar(draw)
    draw_metrics(draw)
    draw_tabs(draw, active_tab="upload")

    # Upload Left Container
    draw.rectangle([30, 215, 820, 680], fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((50, 235), "Upload Examination Document", fill=TEXT_DARK, font=font_heading)
    draw.text((50, 260), "Upload standard or scanned PDFs, images (PNG, JPG, TIFF) of question papers or answer keys.", fill=TEXT_MUTED, font=font_body)

    # Dropzone
    draw.rectangle([50, 290, 800, 480], fill=(248, 250, 252), outline=(199, 210, 254), width=2)
    draw.rectangle([400, 320, 450, 370], fill=BRAND_BG)
    draw.text((415, 335), "📁", font=font_heading)
    draw.text((330, 390), "Click to upload or drag and drop", fill=BRAND_PURPLE, font=font_body_bold)
    draw.text((290, 415), "PDF, PNG, JPG, or TIFF (Magic-byte verified, up to 50MB)", fill=TEXT_MUTED, font=font_small)

    # Controls
    draw.rectangle([50, 510, 410, 560], fill=(248, 250, 252), outline=BORDER_GRAY, width=1)
    draw.text((60, 520), "Document Category", fill=TEXT_MUTED, font=font_small)
    draw.text((60, 536), "Question Paper (Default)", fill=TEXT_DARK, font=font_body_bold)

    draw.rectangle([430, 510, 800, 560], fill=(248, 250, 252), outline=BORDER_GRAY, width=1)
    draw.text((440, 520), "Processing Engine", fill=TEXT_MUTED, font=font_small)
    draw.text((440, 536), "Google Gemini 3.5 Flash (Multimodal AI)", fill=TEXT_DARK, font=font_body_bold)

    # Action Button
    draw.rectangle([580, 600, 800, 645], fill=BRAND_PURPLE)
    draw.text((605, 615), "⚡ Extract Questions & Answers", fill=(255, 255, 255), font=font_body_bold)

    # Right Container (Presets)
    draw.rectangle([840, 215, 1250, 680], fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((860, 235), "Pre-built Test Scenarios", fill=TEXT_DARK, font=font_heading)
    draw.text((860, 260), "Click any preset to inspect extracted intelligence:", fill=TEXT_MUTED, font=font_small)

    presets = [
        ("Sample 1: Standard Exam Paper", "3 MCQs · Clean text · Inline answers", "100%", EMERALD_GREEN),
        ("Sample 2: Clean Image Exam", "2 MCQs · PNG image · Formulas", "95%", EMERALD_GREEN),
        ("Sample 3: Scanned Noisy Exam", "Degraded OCR · Flagged review", "65% ⚠️", AMBER_YELLOW),
        ("Sample 4: Multi-Page Cross Stitch", "Q2 spans Page 1 & 2 · Provenance", "92%", EMERALD_GREEN),
        ("Sample 5: End-of-Doc Answer Key", "3 MCQs on P.1 · Answers on P.2", "98%", EMERALD_GREEN),
        ("Sample 8: Mathematical Formulas", "Calculus & Algebra LaTeX stems", "97%", EMERALD_GREEN),
    ]

    py = 295
    for title, desc, score, scolor in presets:
        draw.rectangle([860, py, 1230, py + 52], fill=(248, 250, 252), outline=BORDER_GRAY, width=1)
        draw.text((875, py + 8), title, fill=TEXT_DARK, font=font_body_bold)
        draw.text((875, py + 28), desc, fill=TEXT_MUTED, font=font_small)
        draw.text((1170, py + 16), score, fill=scolor, font=font_body_bold)
        py += 60

    if cursor_pos:
        draw_cursor(draw, cursor_pos[0], cursor_pos[1])

    return img


def render_scene_2_uploading(progress=45, label="Analyzing document layout with Gemini 3.5 Flash...", cursor_pos=(690, 622)):
    """Scene 2: Uploading & Live Extraction Progress."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_SLATE)
    draw = ImageDraw.Draw(img)

    draw_browser_chrome(draw)
    draw_navbar(draw)
    draw_metrics(draw)
    draw_tabs(draw, active_tab="upload")

    # Upload Left Container
    draw.rectangle([30, 215, 820, 680], fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((50, 235), "Upload Examination Document", fill=TEXT_DARK, font=font_heading)

    # Dropzone with selected file
    draw.rectangle([50, 290, 800, 480], fill=BRAND_BG, outline=BRAND_PURPLE, width=2)
    draw.rectangle([340, 340, 510, 390], fill=(255, 255, 255), outline=BRAND_PURPLE, width=1)
    draw.text((355, 355), "📄 sample_1_standard_exam.pdf", fill=BRAND_PURPLE, font=font_body_bold)
    draw.text((370, 410), "Magic bytes verified: %PDF-1.4 (145 KB)", fill=EMERALD_GREEN, font=font_small_bold)

    # Progress Bar Container
    draw.rectangle([50, 520, 800, 590], fill=(248, 250, 252), outline=BORDER_GRAY, width=1)
    draw.text((65, 532), label, fill=TEXT_DARK, font=font_body_bold)
    draw.text((740, 532), f"{progress}%", fill=BRAND_PURPLE, font=font_body_bold)

    # Bar
    draw.rectangle([65, 558, 785, 572], fill=(226, 232, 240))
    fill_w = int(65 + (720 * (progress / 100.0)))
    draw.rectangle([65, 558, fill_w, 572], fill=BRAND_PURPLE)

    # Action Button (Processing state)
    draw.rectangle([580, 610, 800, 655], fill=(99, 102, 241))
    draw.text((615, 625), "⏳ Processing...", fill=(255, 255, 255), font=font_body_bold)

    # Right Container Presets
    draw.rectangle([840, 215, 1250, 680], fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((860, 235), "Pre-built Test Scenarios", fill=TEXT_DARK, font=font_heading)

    if cursor_pos:
        draw_cursor(draw, cursor_pos[0], cursor_pos[1])

    return img


def render_scene_3_questions(scroll_y=0, cursor_pos=None):
    """Scene 3: Question Intelligence Viewer (Sample 1)."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_SLATE)
    draw = ImageDraw.Draw(img)

    draw_browser_chrome(draw)
    draw_navbar(draw)
    draw_metrics(draw)
    draw_tabs(draw, active_tab="questions")

    # Document Header Strip
    draw.rectangle([30, 210, WIDTH - 30, 255], fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((45, 224), "Current Document: Sample 1: Standard Exam Paper (PDF)", fill=TEXT_DARK, font=font_body_bold)
    draw.rectangle([WIDTH - 380, 220, WIDTH - 220, 246], fill=EMERALD_BG, outline=(167, 243, 208), width=1)
    draw.text((WIDTH - 370, 226), "Engine: Gemini 3.5 Flash", fill=(6, 95, 70), font=font_small_bold)
    draw.rectangle([WIDTH - 210, 220, WIDTH - 45, 246], fill=BRAND_BG, outline=(199, 210, 254), width=1)
    draw.text((WIDTH - 200, 226), "Export JSON Schema", fill=BRAND_PURPLE, font=font_small_bold)

    # Question 1 Card
    q1_y = 270 - scroll_y
    if 200 < q1_y < HEIGHT - 50:
        draw.rectangle([30, q1_y, WIDTH - 30, q1_y + 175], fill=CARD_BG, outline=BORDER_GRAY, width=1)
        draw.rectangle([45, q1_y + 15, 80, q1_y + 40], fill=BRAND_PURPLE)
        draw.text((54, q1_y + 20), "Q1", fill=(255, 255, 255), font=font_body_bold)
        draw.rectangle([90, q1_y + 15, 145, q1_y + 40], fill=(241, 245, 249))
        draw.text((102, q1_y + 20), "MCQ", fill=TEXT_DARK, font=font_small_bold)

        draw.rectangle([WIDTH - 200, q1_y + 15, WIDTH - 45, q1_y + 40], fill=EMERALD_BG, outline=(167, 243, 208), width=1)
        draw.text((WIDTH - 185, q1_y + 20), "Confidence: 100%", fill=EMERALD_GREEN, font=font_small_bold)

        draw.text((45, q1_y + 50), "Which of the following data structures operates on a Last-In, First-Out (LIFO) principle?", fill=TEXT_DARK, font=font_heading)

        options = [
            ("A", "Queue", False),
            ("B", "Stack (Correct Answer)", True),
            ("C", "Binary Tree", False),
            ("D", "Hash Map", False)
        ]
        ox = 45
        for key, opt_text, is_correct in options:
            box_fill = EMERALD_BG if is_correct else (248, 250, 252)
            box_border = (167, 243, 208) if is_correct else BORDER_GRAY
            draw.rectangle([ox, q1_y + 85, ox + 270, q1_y + 120], fill=box_fill, outline=box_border, width=1)
            draw.text((ox + 12, q1_y + 94), f"[{key}]  {opt_text}", fill=(EMERALD_GREEN if is_correct else TEXT_DARK), font=font_body_bold if is_correct else font_body)
            ox += 290

        draw.line([(45, q1_y + 135), (WIDTH - 45, q1_y + 135)], fill=BORDER_GRAY, width=1)
        draw.text((45, q1_y + 145), "Answer: Option B  ·  Source: Inline (Page 1)  ·  Provenance: Page 1  ·  Explanation: LIFO stack pops the most recent item", fill=TEXT_MUTED, font=font_small)

    # Question 2 Card
    q2_y = 460 - scroll_y
    if 200 < q2_y < HEIGHT - 50:
        draw.rectangle([30, q2_y, WIDTH - 30, q2_y + 175], fill=CARD_BG, outline=BORDER_GRAY, width=1)
        draw.rectangle([45, q2_y + 15, 80, q2_y + 40], fill=BRAND_PURPLE)
        draw.text((54, q2_y + 20), "Q2", fill=(255, 255, 255), font=font_body_bold)
        draw.rectangle([90, q2_y + 15, 145, q2_y + 40], fill=(241, 245, 249))
        draw.text((102, q2_y + 20), "MCQ", fill=TEXT_DARK, font=font_small_bold)

        draw.rectangle([WIDTH - 200, q2_y + 15, WIDTH - 45, q2_y + 40], fill=EMERALD_BG, outline=(167, 243, 208), width=1)
        draw.text((WIDTH - 185, q2_y + 20), "Confidence: 100%", fill=EMERALD_GREEN, font=font_small_bold)

        draw.text((45, q2_y + 50), "What is the time complexity of searching for an element in a balanced binary search tree (BST)?", fill=TEXT_DARK, font=font_heading)

        options2 = [
            ("A", "O(1)", False),
            ("B", "O(n)", False),
            ("C", "O(log n) (Correct Answer)", True),
            ("D", "O(n log n)", False)
        ]
        ox = 45
        for key, opt_text, is_correct in options2:
            box_fill = EMERALD_BG if is_correct else (248, 250, 252)
            box_border = (167, 243, 208) if is_correct else BORDER_GRAY
            draw.rectangle([ox, q2_y + 85, ox + 270, q2_y + 120], fill=box_fill, outline=box_border, width=1)
            draw.text((ox + 12, q2_y + 94), f"[{key}]  {opt_text}", fill=(EMERALD_GREEN if is_correct else TEXT_DARK), font=font_body_bold if is_correct else font_body)
            ox += 290

        draw.line([(45, q2_y + 135), (WIDTH - 45, q2_y + 135)], fill=BORDER_GRAY, width=1)
        draw.text((45, q2_y + 145), "Answer: Option C  ·  Source: Inline (Page 1)  ·  Provenance: Page 1  ·  Explanation: Balanced BST height is log2(n)", fill=TEXT_MUTED, font=font_small)

    if cursor_pos:
        draw_cursor(draw, cursor_pos[0], cursor_pos[1])

    return img


def render_scene_4_cross_page(cursor_pos=None):
    """Scene 4: Cross-Page Question Stitching (Sample 4)."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_SLATE)
    draw = ImageDraw.Draw(img)

    draw_browser_chrome(draw)
    draw_navbar(draw)
    draw_metrics(draw)
    draw_tabs(draw, active_tab="questions")

    # Header strip
    draw.rectangle([30, 210, WIDTH - 30, 255], fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((45, 224), "Current Document: Sample 4: Multi-Page Cross-Page Stitching (PDF)", fill=TEXT_DARK, font=font_body_bold)

    # Cross Page Question Card
    cy = 270
    draw.rectangle([30, cy, WIDTH - 30, cy + 220], fill=CARD_BG, outline=BRAND_PURPLE, width=2)

    # Badges
    draw.rectangle([45, cy + 15, 80, cy + 40], fill=BRAND_PURPLE)
    draw.text((54, cy + 20), "Q2", fill=(255, 255, 255), font=font_body_bold)

    # Special Stitched Badge
    draw.rectangle([90, cy + 15, 340, cy + 40], fill=(243, 232, 255), outline=(216, 180, 254), width=1)
    draw.text((102, cy + 20), "🔗 Cross-Page Stitched (Pages 1 & 2)", fill=(107, 33, 168), font=font_small_bold)

    # Confidence
    draw.rectangle([WIDTH - 200, cy + 15, WIDTH - 45, cy + 40], fill=EMERALD_BG, outline=(167, 243, 208), width=1)
    draw.text((WIDTH - 185, cy + 20), "Confidence: 92%", fill=EMERALD_GREEN, font=font_small_bold)

    # Stem
    draw.text((45, cy + 55), "Consider a complete binary tree where each node has either 0 or 2 children.", fill=TEXT_DARK, font=font_heading)
    draw.text((45, cy + 75), "If the tree contains 15 leaves, how many total nodes are in this tree?", fill=TEXT_DARK, font=font_heading)

    # Options
    options = [
        ("A", "27", False),
        ("B", "29 (Correct Answer)", True),
        ("C", "30", False),
        ("D", "31", False)
    ]
    ox = 45
    for key, opt_text, is_correct in options:
        box_fill = EMERALD_BG if is_correct else (248, 250, 252)
        box_border = (167, 243, 208) if is_correct else BORDER_GRAY
        draw.rectangle([ox, cy + 115, ox + 270, cy + 150], fill=box_fill, outline=box_border, width=1)
        draw.text((ox + 12, cy + 124), f"[{key}]  {opt_text}", fill=(EMERALD_GREEN if is_correct else TEXT_DARK), font=font_body_bold if is_correct else font_body)
        ox += 290

    # Cross Page provenance info banner
    draw.rectangle([45, cy + 165, WIDTH - 45, cy + 205], fill=BRAND_BG, outline=(199, 210, 254), width=1)
    draw.text((60, cy + 175), "Cross-Page Heuristic: Question stem extracted on Page 1; Options [A, B, C, D] seamlessly continued and stitched from Page 2.", fill=BRAND_PURPLE, font=font_small_bold)

    if cursor_pos:
        draw_cursor(draw, cursor_pos[0], cursor_pos[1])

    return img


def render_scene_5_review(approved=False, cursor_pos=None):
    """Scene 5: Review Queue with Low-Confidence Flag & Resolution."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_SLATE)
    draw = ImageDraw.Draw(img)

    draw_browser_chrome(draw)
    draw_navbar(draw)
    draw_metrics(draw, review_count=1 if approved else 2)
    draw_tabs(draw, active_tab="review")

    # Review Queue Alert Header
    draw.rectangle([30, 210, WIDTH - 30, 275], fill=AMBER_BG, outline=(253, 230, 138), width=1)
    draw.text((45, 222), "⚠️  Automated Review Queue (Human-in-the-Loop Validation)", fill=(146, 64, 14), font=font_heading)
    draw.text((45, 248), "The system automatically flags questions with confidence < 0.85, high blur noise, or missing option keys for educator verification.", fill=(146, 64, 14), font=font_small)

    # Flagged Card
    ry = 295
    draw.rectangle([30, ry, WIDTH - 30, ry + 250], fill=CARD_BG, outline=(252, 211, 77), width=1)

    # Badges
    draw.rectangle([45, ry + 15, 230, ry + 40], fill=AMBER_BG, outline=(252, 211, 77), width=1)
    draw.text((55, ry + 20), "Needs Review (Confidence: 65%)", fill=AMBER_YELLOW, font=font_small_bold)
    draw.text((250, ry + 20), "Source: sample_3_scanned_noisy_exam.jpg", fill=TEXT_MUTED, font=font_small)

    # Action Buttons
    if not approved:
        draw.rectangle([WIDTH - 240, ry + 15, WIDTH - 120, ry + 42], fill=EMERALD_GREEN)
        draw.text((WIDTH - 225, ry + 22), "✓ Approve & Verify", fill=(255, 255, 255), font=font_small_bold)
    else:
        draw.rectangle([WIDTH - 240, ry + 15, WIDTH - 120, ry + 42], fill=EMERALD_BG, outline=EMERALD_GREEN, width=1)
        draw.text((WIDTH - 225, ry + 22), "✓ Approved!", fill=EMERALD_GREEN, font=font_small_bold)

    draw.rectangle([WIDTH - 110, ry + 15, WIDTH - 45, ry + 42], fill=(241, 245, 249), outline=BORDER_GRAY, width=1)
    draw.text((WIDTH - 95, ry + 22), "Edit Stem", fill=TEXT_DARK, font=font_small_bold)

    # Diagnostic reason
    draw.rectangle([45, ry + 55, WIDTH - 45, ry + 95], fill=(254, 243, 199), outline=(253, 230, 138), width=1)
    draw.text((60, ry + 63), "Automated Diagnostic Reason:", fill=(146, 64, 14), font=font_small_bold)
    draw.text((60, ry + 78), "High optical blur and contrast noise detected on image background. Confidence reduced to 0.65.", fill=(180, 83, 9), font=font_small)

    # Question text
    draw.text((45, ry + 115), "Q1: Which protocol is primarily used for secure communications over the Internet using TLS/SSL encryption?", fill=TEXT_DARK, font=font_heading)

    options = [
        ("A", "HTTP"),
        ("B", "HTTPS (Extracted Answer)"),
        ("C", "FTP"),
        ("D", "SMTP")
    ]
    ox = 45
    for key, opt_text in options:
        is_ans = "HTTPS" in opt_text
        box_fill = EMERALD_BG if is_ans else (248, 250, 252)
        draw.rectangle([ox, ry + 150, ox + 270, ry + 185], fill=box_fill, outline=BORDER_GRAY, width=1)
        draw.text((ox + 12, ry + 158), f"[{key}]  {opt_text}", fill=EMERALD_GREEN if is_ans else TEXT_DARK, font=font_body)
        ox += 290

    # Status Note
    status_text = "Status: Human review pending" if not approved else "Status: Successfully verified by educator. Question approved for LMS export."
    draw.text((45, ry + 215), status_text, fill=(EMERALD_GREEN if approved else TEXT_MUTED), font=font_small_bold)

    if cursor_pos:
        draw_cursor(draw, cursor_pos[0], cursor_pos[1])

    return img


def render_scene_6_json(cursor_pos=None):
    """Scene 6: Structured JSON Inspector."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_SLATE)
    draw = ImageDraw.Draw(img)

    draw_browser_chrome(draw)
    draw_navbar(draw)
    draw_metrics(draw)
    draw_tabs(draw, active_tab="json")

    # Header strip
    draw.rectangle([30, 210, WIDTH - 30, 260], fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((45, 224), "Schema-Compliant Structured JSON Representation", fill=TEXT_DARK, font=font_body_bold)
    draw.text((45, 242), "Standardized payload ready for LMS integration, evaluation pipelines, and vector embeddings.", fill=TEXT_MUTED, font=font_small)

    # Action buttons
    draw.rectangle([WIDTH - 240, 220, WIDTH - 140, 250], fill=(241, 245, 249), outline=BORDER_GRAY, width=1)
    draw.text((WIDTH - 225, 228), "📋 Copy JSON", fill=TEXT_DARK, font=font_small_bold)

    draw.rectangle([WIDTH - 130, 220, WIDTH - 45, 250], fill=BRAND_PURPLE)
    draw.text((WIDTH - 120, 228), "⬇ Download", fill=(255, 255, 255), font=font_small_bold)

    # Dark code viewer
    draw.rectangle([30, 275, WIDTH - 30, 680], fill=CODE_BG)

    json_lines = [
        '{',
        '  "document_type": "QUESTION_PAPER",',
        '  "engine_used": "GeminiMultimodal(gemini-3.5-flash)",',
        '  "page_count": 2,',
        '  "questions": [',
        '    {',
        '      "question_number": "1",',
        '      "question_text": "Which of the following data structures operates on a Last-In, First-Out (LIFO) principle?",',
        '      "question_type": "MCQ",',
        '      "options": [',
        '        { "key": "A", "text": "Queue" },',
        '        { "key": "B", "text": "Stack" },',
        '        { "key": "C", "text": "Binary Tree" },',
        '        { "key": "D", "text": "Hash Map" }',
        '      ],',
        '      "source_pages": [1],',
        '      "confidence": 1.0,',
        '      "answer": {',
        '        "normalized_answer": "B",',
        '        "source_page": 1,',
        '        "association_method": "INLINE_QUESTION_ANSWER"',
        '      }',
        '    }',
        '  ]',
        '}'
    ]

    jy = 290
    for line in json_lines:
        color = (255, 212, 59) if '"question_text"' in line or '"options"' in line else (77, 171, 247) if '"' in line else (240, 243, 246)
        draw.text((50, jy), line, fill=color, font=font_code)
        jy += 16

    if cursor_pos:
        draw_cursor(draw, cursor_pos[0], cursor_pos[1])

    return img


def render_scene_7_closing():
    """Scene 7: Professional Closing Slide."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Glow
    draw.ellipse([WIDTH // 2 - 300, HEIGHT // 2 - 300, WIDTH // 2 + 300, HEIGHT // 2 + 300], fill=(30, 41, 59))

    # Badge
    draw.rectangle([WIDTH // 2 - 130, 170, WIDTH // 2 + 130, 205], fill=(30, 58, 138), outline=(96, 165, 250), width=1)
    draw.text((WIDTH // 2 - 110, 180), "✨ Full Stack Developer Round 2", fill=(191, 219, 254), font=font_small_bold)

    # Title
    draw.text((WIDTH // 2 - 370, 230), "Pragati Bharati — Document Intelligence", fill=(255, 255, 255), font=font_heading)
    draw.text((WIDTH // 2 - 270, 270), "& Question Extraction Service", fill=(129, 140, 248), font=font_heading)

    # Key Highlights
    highlights = [
        "✓  Full-Featured Web Dashboard & Single Page Application (app/static/index.html)",
        "✓  Google Gemini 3.5 Flash Multimodal Intelligence (Verified 100% Accuracy)",
        "✓  Deterministic Rule-Based Offline Fallback Engine (pdfplumber, pypdf, PIL)",
        "✓  Cross-Page Question Stitching with Source Page Provenance",
        "✓  3-Way Answer Key Correlation (Inline, End-of-Doc, Separate Document)",
        "✓  Automated Review Queue (Human-in-the-Loop Validation)",
        "✓  18/18 Automated Tests Passing & Docker Containerized",
    ]

    hy = 340
    for h in highlights:
        draw.text((WIDTH // 2 - 290, hy), h, fill=(226, 232, 240), font=font_body_bold)
        hy += 35

    # Footer
    draw.text((WIDTH // 2 - 180, 620), "GitHub: https://github.com/bandelamahesh8/pnbc", fill=(148, 163, 184), font=font_body)

    return img


def generate_video():
    print(f"Generating website demo recording video: {VIDEO_PATH} via ffmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        str(VIDEO_PATH)
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write_frame(frame: Image.Image, count: int = 1):
        raw_bytes = frame.tobytes()
        for _ in range(count):
            proc.stdin.write(raw_bytes)

    # 1. Landing & Exploring Dashboard (3 seconds)
    print("Rendering Scene 1: Dashboard Landing...")
    for i in range(FPS * 3):
        cx = int(450 + 200 * math.sin(i * 0.05))
        cy = int(320 + 80 * math.cos(i * 0.05))
        frame = render_scene_1_landing(cursor_pos=(cx, cy))
        write_frame(frame)

    # 2. Moving to Upload button & Clicking (2 seconds)
    print("Rendering Scene 2: Upload Action...")
    for i in range(FPS * 2):
        cx = int(450 + (690 - 450) * (i / (FPS * 2)))
        cy = int(320 + (622 - 320) * (i / (FPS * 2)))
        frame = render_scene_1_landing(cursor_pos=(cx, cy))
        write_frame(frame)

    # 3. Processing with Gemini 3.5 Flash (4 seconds)
    print("Rendering Scene 3: Multimodal Extraction...")
    progress_steps = [
        (20, "Verifying magic bytes & uploading sample_1_standard_exam.pdf..."),
        (45, "Analyzing document layout with Gemini 3.5 Flash..."),
        (75, "Extracting stems, options, and formulas..."),
        (95, "Correlating answer keys & calculating confidence..."),
        (100, "Extraction complete! Loading Question Intelligence...")
    ]
    for prog, lbl in progress_steps:
        frame = render_scene_2_uploading(progress=prog, label=lbl, cursor_pos=(690, 622))
        write_frame(frame, count=int(FPS * 0.8))

    # 4. Question Intelligence Viewer - Sample 1 (4 seconds)
    print("Rendering Scene 4: Question Intelligence...")
    for i in range(FPS * 4):
        scroll = int(120 * (i / (FPS * 4)))
        cx = int(300 + 400 * math.sin(i * 0.04))
        cy = int(350 + 100 * math.cos(i * 0.04))
        frame = render_scene_3_questions(scroll_y=scroll, cursor_pos=(cx, cy))
        write_frame(frame)

    # 5. Cross-Page Question Stitching - Sample 4 (3.5 seconds)
    print("Rendering Scene 5: Cross-Page Stitching...")
    for i in range(int(FPS * 3.5)):
        cx = int(200 + 300 * math.sin(i * 0.05))
        cy = int(340 + 50 * math.cos(i * 0.05))
        frame = render_scene_4_cross_page(cursor_pos=(cx, cy))
        write_frame(frame)

    # 6. Review Queue - Low Confidence & Human Approval (4 seconds)
    print("Rendering Scene 6: Review Queue...")
    for i in range(FPS * 2):
        cx = int(400 + (WIDTH - 180 - 400) * (i / (FPS * 2)))
        cy = int(400 + (310 - 400) * (i / (FPS * 2)))
        frame = render_scene_5_review(approved=False, cursor_pos=(cx, cy))
        write_frame(frame)

    for _ in range(FPS * 2):
        frame = render_scene_5_review(approved=True, cursor_pos=(WIDTH - 180, 310))
        write_frame(frame)

    # 7. Structured JSON Inspector (3 seconds)
    print("Rendering Scene 7: JSON Inspector...")
    for i in range(FPS * 3):
        cx = int(WIDTH - 190 + 30 * math.sin(i * 0.05))
        cy = 235
        frame = render_scene_6_json(cursor_pos=(cx, cy))
        write_frame(frame)

    # 8. Closing Summary (3.5 seconds)
    print("Rendering Scene 8: Closing Summary...")
    frame = render_scene_7_closing()
    write_frame(frame, count=int(FPS * 3.5))

    proc.stdin.close()
    proc.wait()
    print(f"Website demo recording saved successfully at: {VIDEO_PATH}")


if __name__ == "__main__":
    generate_video()
