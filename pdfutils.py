from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import streamlit as st
import json


def process_markdown(markdown_text):
    result = []
    lines = markdown_text.strip().splitlines()
    syllabus_title = None  # Add syllabus_title
    title = None
    table_data = []
    headers = []

    for line in lines:
        line = line.strip()

        if line.startswith("# ") and not syllabus_title:  # Syllabus title (only once)
                    syllabus_title = line.lstrip("# ").strip()

        elif "Module: " in line: # Section title
            if title:
                result.append({"syllabus_title": syllabus_title, "title": title, "headers": headers, "table": table_data})
            title = line.lstrip("## ").strip()
            headers = []
            table_data = []

        elif "|" in line and not headers:
            headers = [col.strip() for col in line.split("|")]
            headers = [h for h in headers if h]  # Remove empty headers

        elif line.startswith("|---"):  # Skip separator line
            continue

        elif "|" in line and headers:
            columns = [col.strip() for col in line.split("|")]
            columns = [c for c in columns if c]  # Remove empty columns
            table_data.append(columns)

    if title:
        result.append({"syllabus_title": syllabus_title, "title": title, "headers": headers, "table": table_data})

    return json.dumps(result, indent=4)

def create_pdf(json_string):
    """
    Generate a PDF from a JSON string containing titles and tables.

    Args:
        json_string (str): JSON string containing extracted markdown data.

    Returns:
        str: Filepath of the generated PDF.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filepath = temp_file.name

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), rightMargin=inch, leftMargin=inch, 
                            topMargin=inch, bottomMargin=inch)
    elements = []
    styles = getSampleStyleSheet()

    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON string provided.")
    
    syllabus_title_added = False

    for item in data:
        if not syllabus_title_added:
            syllabus_title = item.get("syllabus_title", "")
            if syllabus_title:
                elements.append(Paragraph(syllabus_title, styles['h1']))
                elements.append(Spacer(1, 12))
                elements.append(Spacer(1, 12))
                syllabus_title_added = True

        title = item.get("title", "")
        headers = item.get("headers", [])
        table_data = item.get("table", [])

        if title:
            elements.append(Paragraph(title, styles['h1']))
            elements.append(Spacer(1, 12))

        if table_data:
            num_columns = len(headers) if headers else 1
            available_width = landscape(A4)[0] - (doc.leftMargin + doc.rightMargin)
            col_widths = [available_width / num_columns] * num_columns

            # Add headers to table data
            table_data.insert(0, headers)

            wrapped_data = [[Paragraph(cell, styles['Normal']) for cell in row] for row in table_data]
            
            table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
            style = TableStyle([
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), 'ON')
            ])
            table.setStyle(style)
            elements.append(table)
            elements.append(Spacer(1, 12))
    
    footer = Paragraph("Generated using the OBE Syllabus Maker created by the WVSU AI Dev Team (c) 2025.", styles['Normal'])
    elements.append(footer)

    doc.build(elements)
    return filepath