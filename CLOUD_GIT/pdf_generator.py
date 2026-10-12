import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_student_result_pdf(student: Dict[str, Any], semester: Dict[str, Any], marks_list: List[Dict[str, Any]], gpa_data: Dict[str, Any]) -> io.BytesIO:
    """
    Generates a clean, professional, verifiable PDF report card for a student.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e293b'),
        alignment=1, # Center
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=1, # Center
        spaceAfter=15
    )
    
    label_style = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#334155'),
    )
    
    bold_label_style = ParagraphStyle(
        'MetaLabelBold',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Institution Header
    story.append(Paragraph("<b>Marks Memo</b>", title_style))
    story.append(Paragraph("Official Semester Grade Report & Academic Transcript", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3b82f6'), spaceAfter=15))
    
    # Student Metadata Table
    student_id = student.get("student_id", student.get("uid", "N/A"))
    student_name = student.get("name", "N/A")
    student_email = student.get("email", "N/A")
    sem_name = semester.get("name", "Semester")
    acad_year = semester.get("academic_year", "")
    
    meta_data = [
        [
            Paragraph("<b>Student Name:</b>", bold_label_style),
            Paragraph(student_name, label_style),
            Paragraph("<b>Semester:</b>", bold_label_style),
            Paragraph(f"{sem_name} {acad_year}".strip(), label_style)
        ],
        [
            Paragraph("<b>Student ID (Roll No):</b>", bold_label_style),
            Paragraph(str(student_id), label_style),
            Paragraph("<b>Student Email:</b>", bold_label_style),
            Paragraph(student_email, label_style)
        ]
    ]
    
    meta_table = Table(meta_data, colWidths=[1.5*inch, 2.2*inch, 1.2*inch, 2.2*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 18))
    
    # Marks Table Header & Rows
    table_data = [
        ["Course Code", "Course Title", "Credits", "Score / 100", "Grade", "Grade Points", "Status"]
    ]
    
    for m in marks_list:
        status_text = "PASS" if m.get("is_pass", False) else "FAIL"
        table_data.append([
            m.get("course_code", "N/A"),
            m.get("course_title", "N/A"),
            str(m.get("credits", 3)),
            f"{m.get('score', 0):.1f}",
            m.get("grade", "F"),
            f"{m.get('grade_points', 0.0):.1f}",
            status_text
        ])
        
    marks_table = Table(table_data, colWidths=[1.1*inch, 2.3*inch, 0.7*inch, 0.9*inch, 0.6*inch, 0.9*inch, 0.7*inch])
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(marks_table)
    story.append(Spacer(1, 20))
    
    # Summary / GPA Box
    gpa = gpa_data.get("gpa", 0.0)
    total_creds = gpa_data.get("total_credits", 0)
    earned_creds = gpa_data.get("earned_credits", 0)
    overall_status = "PASS" if gpa_data.get("all_passed", False) else "FAIL / BACKLOG"
    status_bg = colors.HexColor('#dcfce7') if gpa_data.get("all_passed", False) else colors.HexColor('#fee2e2')
    status_fg = colors.HexColor('#166534') if gpa_data.get("all_passed", False) else colors.HexColor('#991b1b')
    
    summary_data = [
        [
            Paragraph("<b>Total Registered Credits:</b>", bold_label_style),
            Paragraph(str(total_creds), label_style),
            Paragraph("<b>Semester GPA (SGPA):</b>", bold_label_style),
            Paragraph(f"<b><font size='13' color='#2563eb'>{gpa:.2f}</font></b>", label_style)
        ],
        [
            Paragraph("<b>Credits Earned:</b>", bold_label_style),
            Paragraph(str(earned_creds), label_style),
            Paragraph("<b>Final Semester Result:</b>", bold_label_style),
            Paragraph(f"<b><font color='{status_fg.hexval()}'>{overall_status}</font></b>", label_style)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[2.0*inch, 1.5*inch, 2.0*inch, 1.7*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(summary_table)
    
    story.append(Spacer(1, 35))
    # Signature row
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Prepared By / Controller of Exams</b>", ParagraphStyle('Sig', parent=styles['Normal'], fontSize=9, alignment=0)),
            Paragraph("____________________________<br/><b>Dean / Principal</b>", ParagraphStyle('Sig2', parent=styles['Normal'], fontSize=9, alignment=2))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('PADDING', (0,0), (-1,-1), 0)
    ]))
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
