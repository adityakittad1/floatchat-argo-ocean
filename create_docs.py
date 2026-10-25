import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(WORKSPACE_DIR, "FloatChat_Access_Credentials.pdf")
DOCX_PATH = os.path.join(WORKSPACE_DIR, "FloatChat_Access_Credentials.docx")

def build_pdf():
    # Target: Exactly 1 single page with 0.45 inch margins
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch
    )

    styles = getSampleStyleSheet()

    # Brand Colors
    PRIMARY = colors.HexColor("#0A2540")     # Deep oceanic navy
    ACCENT = colors.HexColor("#0077ED")      # Vivid azure cyan
    TEXT_DARK = colors.HexColor("#1A202C")   # Charcoal
    TEXT_MUTED = colors.HexColor("#4A5568")  # Slate gray
    BG_LIGHT = colors.HexColor("#F7FAFC")    # Card background
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=23,
        textColor=PRIMARY,
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=ACCENT,
        alignment=TA_CENTER
    )
    meta_style = ParagraphStyle(
        'MetaInfo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=TA_LEFT
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY
    )
    table_cell_code = ParagraphStyle(
        'TableCellCode',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=ACCENT
    )
    table_cell_text = ParagraphStyle(
        'TableCellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=TEXT_DARK
    )
    credits_style = ParagraphStyle(
        'Credits',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY,
        alignment=TA_CENTER
    )
    sub_credits = ParagraphStyle(
        'SubCredits',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER
    )

    story = []

    # Title block
    story.append(Paragraph("<b>FloatChat: ARGO Ocean Intelligence Platform</b>", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Enterprise Oceanographic Telemetry & AI Discovery System • Access Credentials Reference", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Cloud Web Application:</b> https://floatchat-argo-ocean-t7cjszmnhgb34rt6jnpgvz.streamlit.app/<br/><b>GitHub Source:</b> https://github.com/adityakittad1/floatchat-argo-ocean", meta_style))
    story.append(Spacer(1, 8))

    # Divider
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))

    # System Overview Callout
    callout_data = [[
        Paragraph(
            "<b>Quick Access Instructions:</b> Navigate to the live cloud URL above or run locally on port <code>8501</code>. Enter either the <b>Username</b> or <b>Email Address</b> along with the designated password. FloatChat automatically verifies authentication and activates role-tailored feature sets, autonomous MCP SQL tools, and geospatial analytics.",
            body_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[7.2 * inch])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F7FF")),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#BEE3F8")),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 10))

    # Credentials Table
    story.append(Paragraph("<b>1. PLATFORM AUTHENTICATION MATRIX</b>", section_heading))
    story.append(Spacer(1, 5))

    table_data = [
        [
            Paragraph("System Role", table_header_style),
            Paragraph("Login Username / Email", table_header_style),
            Paragraph("Password", table_header_style),
            Paragraph("Access Privileges & Capabilities", table_header_style)
        ],
        [
            Paragraph("<b>Administrator</b>", table_cell_bold),
            Paragraph("<b>admin</b><br/><font color='#718096'>or admin@argo.com</font>", table_cell_text),
            Paragraph("admin123", table_cell_code),
            Paragraph("Full administrative authority, direct SQLite schema manager, NetCDF ingestion lab, and telemetry console.", table_cell_text)
        ],
        [
            Paragraph("<b>Analyst</b>", table_cell_bold),
            Paragraph("<b>analyst</b><br/><font color='#718096'>or analyst@argo.com</font>", table_cell_text),
            Paragraph("analyst123", table_cell_code),
            Paragraph("Interactive geospatial trajectory visualization, cycle analytics, CSV/Excel data export, and statistical summaries.", table_cell_text)
        ],
        [
            Paragraph("<b>Researcher</b>", table_cell_bold),
            Paragraph("<b>researcher</b><br/><font color='#718096'>or researcher@argo.com</font>", table_cell_text),
            Paragraph("research123", table_cell_code),
            Paragraph("AI Ocean Assistant powered by MCP SQL translation, deep CTD profile queries, and comparative depth models.", table_cell_text)
        ],
        [
            Paragraph("<b>Scientist</b>", table_cell_bold),
            Paragraph("<b>oceanographer</b><br/><font color='#718096'>or oceanographer@argo.com</font>", table_cell_text),
            Paragraph("ocean123", table_cell_code),
            Paragraph("Biogeochemical sensor diagnostic telemetry, 3D salinity/temperature profiles, and water mass stratification analysis.", table_cell_text)
        ]
    ]

    col_widths = [1.35 * inch, 1.85 * inch, 1.1 * inch, 2.9 * inch]
    cred_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    cred_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, ACCENT),
    ]))
    story.append(cred_table)
    story.append(Spacer(1, 10))

    # Key Features Summary
    story.append(Paragraph("<b>2. TECHNICAL ARCHITECTURE & KEY MODULES</b>", section_heading))
    story.append(Spacer(1, 5))

    features_data = [
        [
            Paragraph("<b>MCP Conversational SQL Engine:</b> Translates natural language oceanographic inquiries into optimized SQL queries on <code>argo.db</code>.", table_cell_text),
            Paragraph("<b>Geospatial 3D Trajectory Map:</b> Global interactive scatter maps tracking ARGO float deployment cycles, surface drift, and park depths.", table_cell_text),
        ],
        [
            Paragraph("<b>Interactive CTD Visualizations:</b> Dynamic Plotly graphs depicting Pressure vs Temperature & Salinity profiles with adaptive decimation.", table_cell_text),
            Paragraph("<b>NetCDF Automated Pipeline:</b> Direct binary parser translating Argo <code>.nc</code> profile/tech files into structured relational database tables.", table_cell_text),
        ]
    ]
    feat_table = Table(features_data, colWidths=[3.6 * inch, 3.6 * inch])
    feat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BORDER', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(feat_table)
    story.append(Spacer(1, 12))

    # Footer Divider & Credits
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph("Engineered & Developed by: <b>ADITYA KITTAD</b> &bull; <b>GANESH KAPURE</b> &bull; <b>OM JAISWAL</b>", credits_style))
    story.append(Paragraph("B.Tech Final Year Minor Project &bull; Department of Civil Engineering & Oceanographic Computing &bull; Release v2.4", sub_credits))

    doc.build(story)
    print(f"PDF successfully created: {PDF_PATH}")


def build_docx():
    doc = docx.Document()

    # Set 0.5 inch page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.45)
        section.bottom_margin = Inches(0.45)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Helper function for cell background color
    def set_cell_background(cell, fill_hex):
        tcPr = cell._element.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._element.get_or_add_tcPr()
        tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    run_icon = p_title.add_run("🌊 ")
    run_title = p_title.add_run("FloatChat: ARGO Ocean Intelligence Platform")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(19)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(10, 37, 64)

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(2)
    run_sub = p_sub.add_run("Enterprise Oceanographic Telemetry & AI Discovery System • Access Credentials Reference")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(10)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(0, 119, 237)

    # Meta
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(6)
    r1 = p_meta.add_run("Cloud Web Application: ")
    r1.font.size = Pt(8.5)
    r1.font.bold = True
    r2 = p_meta.add_run("https://floatchat-argo-ocean-t7cjszmnhgb34rt6jnpgvz.streamlit.app/\n")
    r2.font.size = Pt(8.5)
    r2.font.color.rgb = RGBColor(0, 119, 237)
    r3 = p_meta.add_run("GitHub Source Repository: ")
    r3.font.size = Pt(8.5)
    r3.font.bold = True
    r4 = p_meta.add_run("https://github.com/adityakittad1/floatchat-argo-ocean")
    r4.font.size = Pt(8.5)
    r4.font.color.rgb = RGBColor(0, 119, 237)

    # Info Banner Table
    t_banner = doc.add_table(rows=1, cols=1)
    t_banner.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_b = t_banner.cell(0, 0)
    cell_b.width = Inches(7.5)
    set_cell_background(cell_b, "F0F7FF")
    set_cell_margins(cell_b, top=100, bottom=100, left=150, right=150)
    p_b = cell_b.paragraphs[0]
    p_b.paragraph_format.space_before = Pt(0)
    p_b.paragraph_format.space_after = Pt(0)
    r_bi = p_b.add_run("📌 Quick Access Instructions: ")
    r_bi.font.name = "Arial"
    r_bi.font.size = Pt(8.5)
    r_bi.font.bold = True
    r_bi.font.color.rgb = RGBColor(10, 37, 64)
    r_bt = p_b.add_run("Navigate to the cloud URL above or launch locally on port 8501. Enter either the Username or Email Address along with the password. FloatChat automatically initializes an authenticated session with role-tailored feature sets, autonomous MCP SQL tools, and geospatial analytics.")
    r_bt.font.name = "Arial"
    r_bt.font.size = Pt(8.5)
    r_bt.font.color.rgb = RGBColor(26, 32, 44)

    # Spacing
    # Spacing
    p_space1 = doc.add_paragraph()
    p_space1.paragraph_format.space_before = Pt(5)
    p_space1.paragraph_format.space_after = Pt(2)
    r_sec1 = p_space1.add_run("1. PLATFORM AUTHENTICATION MATRIX")
    r_sec1.font.name = "Arial"
    r_sec1.font.size = Pt(11)
    r_sec1.font.bold = True
    r_sec1.font.color.rgb = RGBColor(10, 37, 64)

    # Credentials Table
    table_creds = doc.add_table(rows=5, cols=4)
    table_creds.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["System Role", "Login Username / Email", "Password", "Access Privileges & Capabilities"]
    col_widths_docx = [Inches(1.4), Inches(1.9), Inches(1.1), Inches(3.1)]

    hdr_cells = table_creds.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].width = col_widths_docx[i]
        set_cell_background(hdr_cells[i], "0A2540")
        set_cell_margins(hdr_cells[i], top=90, bottom=90, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.font.name = "Arial"
        run.font.size = Pt(8.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("Administrator", "admin\n(or admin@argo.com)", "admin123", "Full administrative authority, direct SQLite schema manager, NetCDF ingestion lab, and telemetry console."),
        ("Analyst", "analyst\n(or analyst@argo.com)", "analyst123", "Interactive geospatial trajectory visualization, cycle analytics, CSV/Excel data export, and statistical summaries."),
        ("Researcher", "researcher\n(or researcher@argo.com)", "research123", "AI Ocean Assistant powered by MCP SQL translation, deep CTD profile queries, and comparative depth models."),
        ("Scientist", "oceanographer\n(or oceanographer@argo.com)", "ocean123", "Biogeochemical sensor diagnostic telemetry, 3D salinity/temperature profiles, and water mass stratification analysis.")
    ]

    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table_creds.rows[row_idx].cells
        bg_color = "FFFFFF" if row_idx % 2 != 0 else "F7FAFC"
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].width = col_widths_docx[col_idx]
            set_cell_background(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=80, bottom=80, left=120, right=120)
            p = row_cells[col_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(8)
            if col_idx == 0:
                run.font.bold = True
                run.font.color.rgb = RGBColor(10, 37, 64)
            elif col_idx == 2:
                run.font.name = "Courier New"
                run.font.bold = True
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(0, 119, 237)
            else:
                run.font.color.rgb = RGBColor(26, 32, 44)

    # Set light borders for table
    tblPr = table_creds._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="0077ED"/>'
            f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'</w:tblBorders>'
        )
        tblPr[0].append(borders)

    # Architecture Section
    p_space2 = doc.add_paragraph()
    p_space2.paragraph_format.space_before = Pt(6)
    p_space2.paragraph_format.space_after = Pt(2)
    r_sec2 = p_space2.add_run("2. TECHNICAL ARCHITECTURE & KEY MODULES")
    r_sec2.font.name = "Arial"
    r_sec2.font.size = Pt(11)
    r_sec2.font.bold = True
    r_sec2.font.color.rgb = RGBColor(10, 37, 64)

    # Features Grid (2x2 table)
    table_feat = doc.add_table(rows=2, cols=2)
    table_feat.alignment = WD_TABLE_ALIGNMENT.CENTER
    feat_data = [
        ("MCP Conversational SQL Engine", "Translates natural language oceanographic inquiries into optimized SQL queries on argo.db.",
         "Geospatial 3D Trajectory Map", "Global interactive scatter maps tracking ARGO float deployment cycles, surface drift, and park depths."),
        ("Interactive CTD Visualizations", "Dynamic Plotly graphs depicting Pressure vs Temperature & Salinity profiles with downsampling.",
         "NetCDF Automated Pipeline", "Direct binary parser translating Argo .nc profile/tech files into structured relational tables.")
    ]

    for r_idx, (t1, d1, t2, d2) in enumerate(feat_data):
        cells = table_feat.rows[r_idx].cells
        for c_idx, (t, d) in enumerate([(t1, d1), (t2, d2)]):
            cell = cells[c_idx]
            cell.width = Inches(3.75)
            set_cell_background(cell, "FFFFFF")
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r_head = p.add_run(t + "\n")
            r_head.font.name = "Arial"
            r_head.font.size = Pt(8)
            r_head.font.bold = True
            r_head.font.color.rgb = RGBColor(10, 37, 64)
            r_desc = p.add_run(d)
            r_desc.font.name = "Arial"
            r_desc.font.size = Pt(7.5)
            r_desc.font.color.rgb = RGBColor(74, 85, 104)

    tblPr_f = table_feat._element.xpath('w:tblPr')
    if tblPr_f:
        borders_f = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'</w:tblBorders>'
        )
        tblPr_f[0].append(borders_f)

    # Credits footer
    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(8)
    p_foot.paragraph_format.space_after = Pt(1)
    r_cr = p_foot.add_run("Engineered & Developed by: ADITYA KITTAD • GANESH KAPURE • OM JAISWAL")
    r_cr.font.name = "Arial"
    r_cr.font.size = Pt(8.5)
    r_cr.font.bold = True
    r_cr.font.color.rgb = RGBColor(10, 37, 64)

    p_subfoot = doc.add_paragraph()
    p_subfoot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subfoot.paragraph_format.space_before = Pt(0)
    p_subfoot.paragraph_format.space_after = Pt(0)
    r_sub = p_subfoot.add_run("B.Tech Final Year Minor Project • Department of Civil Engineering & Oceanographic Computing • Release v2.4")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(7.5)
    r_sub.font.color.rgb = RGBColor(113, 128, 150)

    doc.save(DOCX_PATH)
    print(f"DOCX successfully created: {DOCX_PATH}")

if __name__ == "__main__":
    build_pdf()
    build_docx()
