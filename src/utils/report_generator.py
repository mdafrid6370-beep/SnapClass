import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


def generate_excel_report(summary_df, raw_df, subject_name="All Subjects"):
    """
    Generates a multi-tab Excel workbook (.xlsx) containing Student Summary and Detailed Logs.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Student Summary
        summary_df.to_excel(writer, sheet_name='Student Summary', index=False)
        
        # Sheet 2: Detailed Logs
        raw_df.to_excel(writer, sheet_name='Detailed Attendance Logs', index=False)
        
        # Auto-adjust column widths for both sheets
        for sheetname in writer.sheets:
            worksheet = writer.sheets[sheetname]
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)
                
    output.seek(0)
    return output.getvalue()


def generate_pdf_report(summary_df, teacher_name="Instructor", subject_name="Classroom Attendance Report"):
    """
    Generates a formatted PDF document report (.pdf) for official school administration submission.
    """
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#2E1065'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#4B5563'),
        spaceAfter=15
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11
    )

    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title & Header
    story.append(Paragraph("SnapClass — Official Attendance Report", title_style))
    meta_text = f"<b>Course/Subject:</b> {subject_name} | <b>Instructor:</b> {teacher_name} | <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(meta_text, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#5865F2'), spaceAfter=15))

    # Calculate Overview Metrics
    total_students = len(summary_df)
    avg_attendance = summary_df['Attendance %'].mean() if not summary_df.empty else 0.0
    at_risk_count = len(summary_df[summary_df['Attendance %'] < 75.0]) if not summary_df.empty else 0

    metrics_data = [
        [
            Paragraph(f"<b>Total Enrolled Students</b><br/><font size=14 color='#5865F2'><b>{total_students}</b></font>", cell_style),
            Paragraph(f"<b>Average Attendance Rate</b><br/><font size=14 color='#166534'><b>{avg_attendance:.1f}%</b></font>", cell_style),
            Paragraph(f"<b>Shortage Risk (<75%)</b><br/><font size=14 color='#991B1B'><b>{at_risk_count}</b></font>", cell_style)
        ]
    ]

    metrics_table = Table(metrics_data, colWidths=[175, 175, 175])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor('#E5E7EB')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))

    story.append(metrics_table)
    story.append(Spacer(1, 20))

    # Student Summary Table
    story.append(Paragraph("<b>Student Roster & Exam Eligibility Summary</b>", styles['Heading3']))
    story.append(Spacer(1, 8))

    table_data = [
        [
            Paragraph("<b>Student ID</b>", cell_bold),
            Paragraph("<b>Student Name</b>", cell_bold),
            Paragraph("<b>Attended</b>", cell_bold),
            Paragraph("<b>Total</b>", cell_bold),
            Paragraph("<b>Attendance %</b>", cell_bold),
            Paragraph("<b>Exam Status</b>", cell_bold),
        ]
    ]

    for _, row in summary_df.iterrows():
        pct = row.get('Attendance %', 0)
        is_eligible = pct >= 75.0
        status_str = "<font color='#166534'><b>Eligible</b></font>" if is_eligible else "<font color='#991B1B'><b>Shortage Alert</b></font>"
        
        table_data.append([
            Paragraph(str(row.get('Student ID', '')), cell_style),
            Paragraph(str(row.get('Student Name', '')), cell_style),
            Paragraph(str(row.get('Classes_Attended', 0)), cell_style),
            Paragraph(str(row.get('Total_Classes', 0)), cell_style),
            Paragraph(f"{pct}%", cell_style),
            Paragraph(status_str, cell_style),
        ])

    summary_table = Table(table_data, colWidths=[85, 140, 65, 65, 80, 90])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5865F2')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 30))

    # Official Signature Line
    sig_data = [
        [
            Paragraph("<b>Instructor Signature:</b> _______________________", cell_style),
            Paragraph("<b>Department Approval:</b> _______________________", cell_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[260, 265])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(sig_table)

    doc.build(story)
    output.seek(0)
    return output.getvalue()
