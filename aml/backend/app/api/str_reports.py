import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user, RequireRole
from app.models.models import STRReport, Case, Customer, User
from app.schemas.schemas import STRCreate, STRResponse

router = APIRouter(prefix="/str", tags=["STR Generation"])

REPORTS_DIR = "reports"

@router.get("", response_model=List[STRResponse])
def get_str_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(STRReport).order_by(STRReport.created_at.desc()).all()

@router.post("/generate", response_model=STRResponse)
def generate_str_report(
    payload: STRCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["INVESTIGATOR", "OFFICER", "ADMIN"]))
):
    case_obj = db.query(Case).filter(Case.case_id == payload.case_id).first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")

    customer = db.query(Customer).filter(Customer.customer_id == case_obj.lead_customer_id).first()
    cust_name = customer.full_name if customer else "Unknown Customer"

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_id = f"STR_{uuid.uuid4().hex[:8].upper()}"
    fiu_ref = f"FIU-IND-2026-{uuid.uuid4().hex[:6].upper()}"
    pdf_filename = f"{report_id}_{case_obj.case_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    # Generate PDF using ReportLab or Text fallback
    #
    # Layout: a monochrome, boxed-field regulatory form (closest to how real
    # STR/SAR filings are laid out — structured reference fields rather than
    # a decorative letterhead), with a ruled frame around each page.
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
        from reportlab.pdfgen import canvas
        import ast

        # Monochrome palette — matches the register of an actual regulatory filing.
        INK        = colors.HexColor("#0E0E0E")  # headings, primary text, heavy rules
        MUTED      = colors.HexColor("#444444")  # field labels, footer, classification line
        LIGHT_RULE = colors.HexColor("#999999")  # thin field gridlines

        FRAME_MARGIN = 26   # outer double-rule frame, drawn on every page
        CONTENT_MARGIN = 46 # story content margin (inside the frame)
        PAGE_W, PAGE_H = letter

        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_page_furniture(num_pages)
                    super().showPage()
                super().save()

            def draw_page_furniture(self, page_count):
                self.saveState()

                # Double-rule frame — outer heavy rule + inner hairline, like a printed form.
                self.setStrokeColor(INK)
                self.setLineWidth(1.1)
                self.rect(FRAME_MARGIN, FRAME_MARGIN, PAGE_W - 2 * FRAME_MARGIN, PAGE_H - 2 * FRAME_MARGIN)
                self.setLineWidth(0.4)
                self.rect(FRAME_MARGIN + 3, FRAME_MARGIN + 3, PAGE_W - 2 * (FRAME_MARGIN + 3), PAGE_H - 2 * (FRAME_MARGIN + 3))

                # Footer: classification + pagination, inside the frame.
                self.setFont("Helvetica", 7)
                self.setFillColor(MUTED)
                self.setStrokeColor(LIGHT_RULE)
                self.setLineWidth(0.5)
                footer_y = FRAME_MARGIN + 16
                self.line(CONTENT_MARGIN, footer_y + 8, PAGE_W - CONTENT_MARGIN, footer_y + 8)
                self.drawString(CONTENT_MARGIN, footer_y, "CLASSIFICATION: RESTRICTED — FIU INTERNAL USE ONLY. Unauthorized disclosure is prohibited under PMLA, 2002.")
                self.drawRightString(PAGE_W - CONTENT_MARGIN, footer_y, f"Page {self._pageNumber} of {page_count}")
                self.restoreState()

        def cell(text: str, style: ParagraphStyle) -> Paragraph:
            return Paragraph(text, style)

        def section(number: str, heading_text: str, content_flowables: list) -> list:
            res = [
                Paragraph(f"{number}.", clause_num_style),
                Paragraph(heading_text.upper(), section_heading_style),
                HRFlowable(width="100%", thickness=0.5, color=LIGHT_RULE, spaceBefore=2, spaceAfter=7)
            ]
            res.extend(content_flowables)
            return res

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            leftMargin=CONTENT_MARGIN,
            rightMargin=CONTENT_MARGIN,
            topMargin=CONTENT_MARGIN,
            bottomMargin=CONTENT_MARGIN + 12
        )
        story = []

        form_no_style = ParagraphStyle(
            "FormNo", fontName="Courier", fontSize=7.5, leading=10,
            textColor=MUTED, alignment=TA_RIGHT, spaceAfter=10
        )
        main_title_style = ParagraphStyle(
            "MainTitle", fontName="Times-Bold", fontSize=17, leading=21,
            textColor=INK, alignment=TA_CENTER, spaceAfter=3
        )
        legal_sub_style = ParagraphStyle(
            "LegalSub", fontName="Helvetica", fontSize=9, leading=12,
            textColor=MUTED, alignment=TA_CENTER, spaceAfter=12
        )
        section_heading_style = ParagraphStyle(
            "SectionHeading", fontName="Helvetica-Bold", fontSize=10, leading=13,
            textColor=INK, spaceAfter=2
        )
        clause_num_style = ParagraphStyle(
            "ClauseNum", fontName="Helvetica-Bold", fontSize=8, leading=10,
            textColor=MUTED, spaceAfter=0
        )
        body_style = ParagraphStyle(
            "BodySerif", fontName="Times-Roman", fontSize=10.2, leading=15,
            textColor=INK, alignment=TA_JUSTIFY, spaceAfter=12
        )
        field_lbl_style = ParagraphStyle(
            "FieldLabel", fontName="Helvetica-Bold", fontSize=7, leading=9,
            textColor=MUTED, spaceAfter=2
        )
        field_val_style = ParagraphStyle(
            "FieldVal", fontName="Courier-Bold", fontSize=9.5, leading=12,
            textColor=INK
        )

        # 1. Header
        formatted_date = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
        story.append(cell(f"FORM STR-1 / REV. 2026 &nbsp;&nbsp;·&nbsp;&nbsp; {fiu_ref}", form_no_style))
        story.append(cell("SUSPICIOUS TRANSACTION REPORT", main_title_style))
        story.append(cell("Filed pursuant to the Prevention of Money Laundering Act, 2002", legal_sub_style))
        story.append(HRFlowable(width="100%", thickness=1.4, color=INK, spaceBefore=0, spaceAfter=1))
        story.append(HRFlowable(width="100%", thickness=0.4, color=INK, spaceBefore=1, spaceAfter=14))

        # 2. Boxed reference-field grid (structured form fields, not a letterhead table)
        def field(label: str, value: str) -> list:
            return [cell(label.upper(), field_lbl_style), cell(value, field_val_style)]

        field_grid = [
            field("Report Reference", fiu_ref) + field("Date Generated", formatted_date),
            field("Case ID", case_obj.case_id) + field("Priority Level", case_obj.priority),
            field("Lead Subject", cust_name) + field("National ID", customer.national_id if customer else "N/A"),
            field("AML Risk Score", f"{case_obj.meta_risk_score}%") + field("Generated By", current_user.full_name),
        ]

        t = Table(field_grid, colWidths=[130, 165, 130, 105])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_RULE),
            ('BOX', (0, 0), (-1, -1), 1.1, INK),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 9),
            ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ]))
        story.append(t)
        story.append(Spacer(1, 18))

        # 3. Content Sections (numbered clauses)
        story.extend(section("1", "Investigation Narrative Summary", [
            cell(payload.narrative_summary, body_style),
        ]))

        # Parse typologies nicely
        typo_raw = case_obj.correlated_typologies or ""
        if isinstance(typo_raw, str):
            try:
                parsed = ast.literal_eval(typo_raw)
                if isinstance(parsed, list):
                    typo_str = ", ".join(parsed)
                else:
                    typo_str = str(parsed)
            except Exception:
                typo_str = typo_raw.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        else:
            typo_str = str(typo_raw)

        story.extend(section("2", "Correlated Typologies & Graph Evidence", [
            cell(f"Correlated typologies flagged: {typo_str}.", body_style),
            cell(f"Case summary: {case_obj.summary}", body_style)
        ]))

        doc.build(story, canvasmaker=NumberedCanvas)
    except Exception as ex:
        # Fallback text creation
        with open(pdf_path, "w") as f:
            f.write(f"FIU SUSPICIOUS TRANSACTION REPORT\nFIU Ref: {fiu_ref}\nCase ID: {case_obj.case_id}\nCustomer: {cust_name}\nNarrative:\n{payload.narrative_summary}")

    new_str = STRReport(
        report_id=report_id,
        case_id=payload.case_id,
        fiu_ref_number=fiu_ref,
        narrative_summary=payload.narrative_summary,
        status="DRAFT",
        generated_by=current_user.user_id,
        pdf_path=pdf_path,
        created_at=datetime.utcnow()
    )
    db.add(new_str)
    db.commit()
    return new_str

@router.post("/{report_id}/approve")
def approve_str_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["OFFICER", "ADMIN"]))
):
    report = db.query(STRReport).filter(STRReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="STR Report not found")
    
    report.status = "APPROVED"
    report.approved_by = current_user.user_id
    db.commit()
    return {"message": "STR Report officially approved for FIU submission", "report_id": report_id}

@router.get("/{report_id}/download")
def download_str_pdf(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(STRReport).filter(STRReport.report_id == report_id).first()
    if not report or not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="STR PDF report file not found")
    
    return FileResponse(report.pdf_path, filename=os.path.basename(report.pdf_path), media_type="application/pdf")
