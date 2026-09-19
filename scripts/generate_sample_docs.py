import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors

SAMPLES_DIR = Path("samples/input")
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_1_standard_exam():
    """Sample 1: Standard 2-page exam with MCQs and inline answer key."""
    doc = SimpleDocTemplate(str(SAMPLES_DIR / "sample_1_standard_exam.pdf"), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = styles["Heading1"]
    title_style.alignment = 1
    story.append(Paragraph("<b>Pragati Bharati National Assessment Examination</b>", title_style))
    story.append(Spacer(1, 15))

    q1_text = "<b>1.</b> Which of the following data structures operates on a Last-In, First-Out (LIFO) principle?"
    story.append(Paragraph(q1_text, styles["Normal"]))
    story.append(Paragraph("(A) Queue", styles["Normal"]))
    story.append(Paragraph("(B) Stack", styles["Normal"]))
    story.append(Paragraph("(C) Binary Tree", styles["Normal"]))
    story.append(Paragraph("(D) Hash Map", styles["Normal"]))
    story.append(Spacer(1, 15))

    q2_text = "<b>2.</b> What is the time complexity of searching for an element in a balanced binary search tree with n nodes?"
    story.append(Paragraph(q2_text, styles["Normal"]))
    story.append(Paragraph("(A) O(1)", styles["Normal"]))
    story.append(Paragraph("(B) O(n)", styles["Normal"]))
    story.append(Paragraph("(C) O(log n)", styles["Normal"]))
    story.append(Paragraph("(D) O(n log n)", styles["Normal"]))
    story.append(Spacer(1, 15))

    story.append(PageBreak())

    q3_text = "<b>3.</b> In relational database management systems, which normal form eliminates transitive dependencies?"
    story.append(Paragraph(q3_text, styles["Normal"]))
    story.append(Paragraph("(A) First Normal Form (1NF)", styles["Normal"]))
    story.append(Paragraph("(B) Second Normal Form (2NF)", styles["Normal"]))
    story.append(Paragraph("(C) Third Normal Form (3NF)", styles["Normal"]))
    story.append(Paragraph("(D) Boyce-Codd Normal Form (BCNF)", styles["Normal"]))
    story.append(Spacer(1, 30))

    # Inline Answer Key Section
    story.append(Paragraph("<b>=== ANSWER KEY ===</b>", styles["Heading2"]))
    story.append(Paragraph("1. B", styles["Normal"]))
    story.append(Paragraph("2. C", styles["Normal"]))
    story.append(Paragraph("3. C", styles["Normal"]))

    doc.build(story)
    print("Created sample_1_standard_exam.pdf")


def create_sample_2_image():
    """Sample 2: Image containing exam questions."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.text((50, 40), "Pragati Bharati - Science Quiz (Snapshot)", fill=(0, 0, 128))

    # Question 1
    draw.text((50, 90), "1. What is the chemical symbol for Gold?", fill=(0, 0, 0))
    draw.text((70, 120), "(A) Ag", fill=(50, 50, 50))
    draw.text((70, 145), "(B) Au", fill=(50, 50, 50))
    draw.text((70, 170), "(C) Fe", fill=(50, 50, 50))
    draw.text((70, 195), "(D) Pb", fill=(50, 50, 50))

    # Question 2
    draw.text((50, 240), "2. Which organelle is known as the powerhouse of the cell?", fill=(0, 0, 0))
    draw.text((70, 270), "(A) Ribosome", fill=(50, 50, 50))
    draw.text((70, 295), "(B) Nucleus", fill=(50, 50, 50))
    draw.text((70, 320), "(C) Mitochondria", fill=(50, 50, 50))
    draw.text((70, 345), "(D) Golgi Apparatus", fill=(50, 50, 50))

    # Answers
    draw.text((50, 420), "=== ANSWER KEY ===", fill=(128, 0, 0))
    draw.text((50, 450), "1. B", fill=(0, 0, 0))
    draw.text((50, 480), "2. C", fill=(0, 0, 0))

    img.save(str(SAMPLES_DIR / "sample_2_question_paper.png"))
    print("Created sample_2_question_paper.png")


def create_sample_3_scanned_low_quality():
    """Sample 3: Low quality / degraded document simulation."""
    # Create a small low-res image with compression artifacts
    img = Image.new("RGB", (320, 240), color=(240, 240, 230))
    draw = ImageDraw.Draw(img)

    draw.text((10, 10), "Exam Sample (Low Res)", fill=(80, 80, 80))
    draw.text((10, 40), "Q.1 Identify the primary color:", fill=(70, 70, 70))
    draw.text((20, 65), "(A) Blue", fill=(90, 90, 90))
    draw.text((20, 85), "(B) Orange", fill=(90, 90, 90))
    draw.text((10, 120), "Ans: (A)", fill=(80, 80, 80))

    img.save(str(SAMPLES_DIR / "sample_3_scanned_low_quality.jpg"), quality=20)
    print("Created sample_3_scanned_low_quality.jpg")


def create_sample_4_multi_questions():
    """Sample 4: Document with 10+ questions and diverse numbering formats."""
    doc = SimpleDocTemplate(str(SAMPLES_DIR / "sample_4_multi_questions.pdf"), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Comprehensive General Knowledge & Logic Test</b>", styles["Heading1"]))
    story.append(Spacer(1, 10))

    questions = [
        ("1.", "What is the capital city of Australia?", ["(A) Sydney", "(B) Melbourne", "(C) Canberra", "(D) Brisbane"]),
        ("Q.2", "Which planet in our solar system is known as the Red Planet?", ["(A) Venus", "(B) Mars", "(C) Jupiter", "(D) Saturn"]),
        ("Question 3:", "Which element has the highest electrical conductivity?", ["(A) Copper", "(B) Silver", "(C) Gold", "(D) Aluminum"]),
        ("4)", "In which year did the Apollo 11 mission land on the Moon?", ["(A) 1965", "(B) 1969", "(C) 1971", "(D) 1975"]),
        ("5.", "Who wrote the play 'Hamlet'?", ["(A) Charles Dickens", "(B) William Shakespeare", "(C) Mark Twain", "(D) Jane Austen"]),
        ("Q.6", "What is the primary gas found in Earth's atmosphere?", ["(A) Oxygen", "(B) Carbon Dioxide", "(C) Nitrogen", "(D) Hydrogen"]),
        ("7.", "What is the boiling point of water at standard sea level atmospheric pressure?", ["(A) 90°C", "(B) 100°C", "(C) 110°C", "(D) 120°C"]),
        ("Question 8:", "Which mathematical constant represents the ratio of a circle's circumference to its diameter?", ["(A) e", "(B) phi", "(C) pi", "(D) sqrt(2)"]),
        ("9)", "Which protocol is primarily used for secure communication over the Internet?", ["(A) HTTP", "(B) FTP", "(C) HTTPS", "(D) SMTP"]),
        ("10.", "How many bytes are in a standard gigabyte (decimal)?", ["(A) 10^6", "(B) 10^9", "(C) 2^20", "(D) 2^40"]),
        ("11(a)", "What is the speed of light in vacuum (approximate)?", ["(A) 3 x 10^8 m/s", "(B) 3 x 10^6 m/s", "(C) 1.5 x 10^8 m/s", "(D) 3 x 10^5 m/s"]),
    ]

    for num, stem, opts in questions:
        story.append(Paragraph(f"<b>{num}</b> {stem}", styles["Normal"]))
        for opt in opts:
            story.append(Paragraph(opt, styles["Normal"]))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>=== ANSWER KEY ===</b>", styles["Heading2"]))
    ans_key = ["1. C", "2. B", "3. B", "4. B", "5. B", "6. C", "7. B", "8. C", "9. C", "10. B", "11. A"]
    for a in ans_key:
        story.append(Paragraph(a, styles["Normal"]))

    doc.build(story)
    print("Created sample_4_multi_questions.pdf")


def create_sample_5_cross_page():
    """Sample 5: Question spanning multiple pages."""
    doc = SimpleDocTemplate(str(SAMPLES_DIR / "sample_5_cross_page.pdf"), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Advanced Distributed Systems Examination</b>", styles["Heading1"]))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>1.</b> Consider a distributed consensus algorithm executing across 5 asynchronous nodes.", styles["Normal"]))
    story.append(Paragraph("Under the FLP impossibility result, what guarantee can be provided in an asynchronous network subject to crash failures?", styles["Normal"]))
    story.append(Paragraph("(A) Absolute liveness and safety simultaneously under all conditions", styles["Normal"]))
    story.append(Paragraph("(B) Deterministic consensus within bounded time O(n)", styles["Normal"]))

    # Page break right in the middle of Question 1's options!
    story.append(PageBreak())

    story.append(Paragraph("(C) Safety is preserved, but termination/liveness cannot be guaranteed deterministically", styles["Normal"]))
    story.append(Paragraph("(D) Fault tolerance up to n/2 Byzantine nodes without cryptographic signatures", styles["Normal"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>2.</b> Which consistency model requires that all operations appear to take effect at a specific point in time?", styles["Normal"]))
    story.append(Paragraph("(A) Eventual Consistency", styles["Normal"]))
    story.append(Paragraph("(B) Causal Consistency", styles["Normal"]))
    story.append(Paragraph("(C) Linearizability", styles["Normal"]))
    story.append(Paragraph("(D) Read-After-Write Consistency", styles["Normal"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>=== ANSWER KEY ===</b>", styles["Heading2"]))
    story.append(Paragraph("1. C", styles["Normal"]))
    story.append(Paragraph("2. C", styles["Normal"]))

    doc.build(story)
    print("Created sample_5_cross_page.pdf")


def create_sample_6_rich_options():
    """Sample 6: Questions with tabular data and mathematical options."""
    doc = SimpleDocTemplate(str(SAMPLES_DIR / "sample_6_rich_options.pdf"), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Database Engineering & Query Optimization</b>", styles["Heading1"]))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>1.</b> Consider the following relational table 'Employees':", styles["Normal"]))
    story.append(Spacer(1, 8))

    table_data = [
        ["EmpID", "Name", "Department", "Salary"],
        ["101", "Alice Smith", "Engineering", "95,000"],
        ["102", "Bob Jones", "Marketing", "72,000"],
        ["103", "Charlie Brown", "Engineering", "88,000"],
    ]
    t = Table(table_data, colWidths=[80, 120, 120, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Which SQL query computes the average salary for the Engineering department?", styles["Normal"]))
    story.append(Paragraph("(A) SELECT AVG(Salary) FROM Employees WHERE Department = 'Engineering';", styles["Normal"]))
    story.append(Paragraph("(B) SELECT SUM(Salary) / COUNT(*) FROM Employees;", styles["Normal"]))
    story.append(Paragraph("(C) SELECT Salary FROM Employees GROUP BY Department;", styles["Normal"]))
    story.append(Paragraph("(D) SELECT MAX(Salary) - MIN(Salary) FROM Employees;", styles["Normal"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>=== ANSWER KEY ===</b>", styles["Heading2"]))
    story.append(Paragraph("1. A", styles["Normal"]))

    doc.build(story)
    print("Created sample_6_rich_options.pdf")


def create_sample_7_and_8_separate_docs():
    """Sample 7: Question paper without answers. Sample 8: Separate Answer Key document."""
    # 7: Question Paper
    doc7 = SimpleDocTemplate(str(SAMPLES_DIR / "sample_7_separate_question_paper.pdf"), pagesize=letter)
    styles = getSampleStyleSheet()
    story7 = []

    story7.append(Paragraph("<b>Standard Mathematics Assessment - Grade 10</b>", styles["Heading1"]))
    story7.append(Spacer(1, 15))

    story7.append(Paragraph("<b>1.</b> If 2x + 5 = 15, what is the value of x?", styles["Normal"]))
    story7.append(Paragraph("(A) 3", styles["Normal"]))
    story7.append(Paragraph("(B) 5", styles["Normal"]))
    story7.append(Paragraph("(C) 7", styles["Normal"]))
    story7.append(Paragraph("(D) 10", styles["Normal"]))
    story7.append(Spacer(1, 15))

    story7.append(Paragraph("<b>2.</b> What is the area of a right-angled triangle with base 6 cm and height 8 cm?", styles["Normal"]))
    story7.append(Paragraph("(A) 14 cm²", styles["Normal"]))
    story7.append(Paragraph("(B) 24 cm²", styles["Normal"]))
    story7.append(Paragraph("(C) 48 cm²", styles["Normal"]))
    story7.append(Paragraph("(D) 56 cm²", styles["Normal"]))

    doc7.build(story7)
    print("Created sample_7_separate_question_paper.pdf")

    # 8: Answer Key Document
    doc8 = SimpleDocTemplate(str(SAMPLES_DIR / "sample_8_separate_answer_key.pdf"), pagesize=letter)
    story8 = []

    story8.append(Paragraph("<b>Official Solutions & Answer Keys - Grade 10 Mathematics</b>", styles["Heading1"]))
    story8.append(Spacer(1, 15))
    story8.append(Paragraph("1. B (Explanation: 2x = 10 => x = 5)", styles["Normal"]))
    story8.append(Paragraph("2. B (Explanation: Area = 1/2 * base * height = 1/2 * 6 * 8 = 24)", styles["Normal"]))

    doc8.build(story8)
    print("Created sample_8_separate_answer_key.pdf")


def create_sample_9_uncertain_low_confidence():
    """Sample 9: Incomplete document triggering low confidence and human review."""
    doc = SimpleDocTemplate(str(SAMPLES_DIR / "sample_9_uncertain_low_confidence.pdf"), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Fragmented / Draft Notes</b>", styles["Heading1"]))
    story.append(Spacer(1, 15))

    # Question with missing options (only 1 option)
    story.append(Paragraph("<b>1.</b> What is ...", styles["Normal"]))
    story.append(Paragraph("(A) Incomplete option only", styles["Normal"]))
    story.append(Spacer(1, 15))

    # Question with very short stem
    story.append(Paragraph("<b>2.</b> Why?", styles["Normal"]))
    story.append(Paragraph("(A) Yes", styles["Normal"]))
    story.append(Paragraph("(B) No", styles["Normal"]))

    doc.build(story)
    print("Created sample_9_uncertain_low_confidence.pdf")


def create_sample_10_invalid_file():
    """Sample 10: Invalid/malicious file with disguised extension."""
    invalid_path = SAMPLES_DIR / "sample_10_malicious_disguised.pdf"
    # Write Windows PE header / dummy binary bytes disguised as PDF
    with open(invalid_path, "wb") as f:
        f.write(b"MZ\x90\x00\x03\x00\x00\x00This is an executable disguised as PDF.")
    print("Created sample_10_malicious_disguised.pdf")


if __name__ == "__main__":
    create_sample_1_standard_exam()
    create_sample_2_image()
    create_sample_3_scanned_low_quality()
    create_sample_4_multi_questions()
    create_sample_5_cross_page()
    create_sample_6_rich_options()
    create_sample_7_and_8_separate_docs()
    create_sample_9_uncertain_low_confidence()
    create_sample_10_invalid_file()
    print("All 10 sample documents generated successfully in samples/input/")
