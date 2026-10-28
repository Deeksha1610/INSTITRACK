from typing import Optional
from datetime import datetime, timezone
from io import BytesIO, StringIO
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
import csv

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

from app.db.session import get_db
from app.core.deps import get_staff, get_auditor
from app.models.user import User, RoleEnum
from app.models.case import Case, CaseStatus, AuditLog
from app.schemas.case import AuditLogOut

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/cases.csv")
def export_cases_csv(
    status: Optional[str] = None,
    institution_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    query = db.query(Case).options(
        joinedload(Case.institution),
        joinedload(Case.assigned_bureau),
        joinedload(Case.assigned_officer),
    )
    if current_user.role == RoleEnum.BUREAU_OFFICER:
        query = query.filter(
            (Case.assigned_officer_id == current_user.id) | (Case.assigned_bureau_id == current_user.bureau_id)
        )
    if status:
        query = query.filter(Case.status == status)
    if institution_id:
        query = query.filter(Case.institution_id == institution_id)

    cases = query.order_by(desc(Case.created_at)).limit(5000).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Case ID", "Title", "Category", "Status", "Priority", "Institution",
        "Institution ID", "Bureau", "Officer", "Overdue", "Created At", "Deadline", "Closed At"
    ])
    for c in cases:
        writer.writerow([
            c.case_id, c.title, c.category.value if c.category else "",
            c.status.value if c.status else "", c.priority.value if c.priority else "",
            c.institution.name if c.institution else "",
            c.institution.institution_id if c.institution else "",
            c.assigned_bureau.name if c.assigned_bureau else "",
            c.assigned_officer.full_name if c.assigned_officer else "",
            "Yes" if c.is_overdue else "No",
            c.created_at.isoformat() if c.created_at else "",
            c.deadline.isoformat() if c.deadline else "",
            c.closed_at.isoformat() if c.closed_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=institack_cases.csv"},
    )


@router.get("/cases.pdf")
def export_cases_pdf(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff),
):
    query = db.query(Case).options(joinedload(Case.institution), joinedload(Case.assigned_bureau))
    if current_user.role == RoleEnum.BUREAU_OFFICER:
        query = query.filter(
            (Case.assigned_officer_id == current_user.id) | (Case.assigned_bureau_id == current_user.bureau_id)
        )
    if status:
        query = query.filter(Case.status == status)
    cases = query.order_by(desc(Case.created_at)).limit(200).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("INSTITRACK — Case Report (Demonstration Data)", styles["Title"]))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [["Case ID", "Title", "Category", "Status", "Institution", "Bureau", "Created"]]
    for c in cases:
        data.append([
            c.case_id,
            (c.title[:40] + "…") if len(c.title) > 40 else c.title,
            (c.category.value[:20] if c.category else ""),
            c.status.value if c.status else "",
            (c.institution.name[:25] if c.institution else ""),
            (c.assigned_bureau.name[:20] if c.assigned_bureau else ""),
            c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Fictional demonstration data for SIH. Not official AICTE records.", styles["Normal"]))
    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=institack_cases.pdf"},
    )


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_auditor),
):
    logs = (
        db.query(AuditLog)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
        .all()
    )
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        result.append({
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at,
            "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role} if user else None,
        })
    return result
