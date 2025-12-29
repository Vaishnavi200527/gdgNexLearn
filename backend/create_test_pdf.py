#!/usr/bin/env python3
"""
Create a proper test PDF file for testing PDF upload functionality
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf():
    """Create a proper PDF file with educational content"""
    filename = "test_educational.pdf"
    c = canvas.Canvas(filename, pagesize=letter)

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Introduction to Machine Learning")

    # Content
    c.setFont("Helvetica", 12)
    y_position = 720
    content = [
        "Machine Learning is a subset of artificial intelligence (AI) that provides",
        "systems the ability to automatically learn and improve from experience",
        "without being explicitly programmed.",
        "",
        "Key Concepts:",
        "• Supervised Learning: Learning from labeled training data",
        "• Unsupervised Learning: Finding patterns in unlabeled data",
        "• Neural Networks: Computing systems inspired by biological neural networks",
        "• Deep Learning: A subset of machine learning using deep neural networks",
        "",
        "Applications:",
        "• Image recognition and computer vision",
        "• Natural language processing",
        "• Recommendation systems",
        "• Predictive analytics"
    ]

    for line in content:
        if line.strip() == "":
            y_position -= 15
            continue
        c.drawString(100, y_position, line)
        y_position -= 15

    c.save()
    print(f"Created educational test PDF: {filename}")
    return filename

if __name__ == "__main__":
    create_test_pdf()
