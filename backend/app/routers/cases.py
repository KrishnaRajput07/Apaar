"""Cases router — list, detail, officer decision, assign."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user, require_role
from ..models import Case, Institution

router = APIRouter(prefix="/cases", tags=["cases"])


class OfficerDecision(BaseModel):
    decision: str           # Resolved — no issue | Resolved — action taken | Escalate
    rationale: str
    case_id: str


@router.get("/")
def list_cases(
    status: str | None = None,
    severity: str | None = None,
    institution_id: str | None = None,
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(Case)
    if status:
        q = q.filter(Case.status == status)
    if severity:
        q = q.filter(Case.severity == severity)
    if institution_id:
        q = q.filter(Case.institution_id == institution_id)
    cases = q.order_by(Case.severity.desc(), Case.opened_at.desc()).offset(skip).limit(limit).all()
    return [_case_summary(db, c) for c in cases]


@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        # try by case_ref
        c = db.query(Case).filter(Case.case_ref == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_detail(db, c)


@router.post("/{case_id}/decision")
def record_decision(
    case_id: str,
    req: OfficerDecision,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("officer")),
):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        c = db.query(Case).filter(Case.case_ref == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    c.status = "Resolved" if "Resolved" in req.decision else "Escalated"
    c.outcome = req.decision
    c.rationale = req.rationale
    c.closed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(c)

    return {
        "status": "recorded",
        "case_id": c.id,
        "case_ref": c.case_ref,
        "outcome": c.outcome,
        "closed_at": c.closed_at.isoformat() if c.closed_at else None,
        "audit_ref": f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
    }


@router.post("/{case_id}/assign")
def assign_case(
    case_id: str,
    officer_name: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("officer")),
):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    c.assigned_to = officer_name
    db.commit()
    return {"status": "assigned", "case_id": case_id, "assigned_to": officer_name}


def _case_summary(db: Session, c: Case) -> dict:
    inst = db.query(Institution).filter(Institution.id == c.institution_id).first()
    return {
        "id": c.id, "case_ref": c.case_ref,
        "case_type": c.case_type, "severity": c.severity,
        "institution_id": c.institution_id,
        "institution_name": inst.name if inst else "",
        "subject_type": c.subject_type, "subject_id": c.subject_id,
        "reason_codes": c.reason_codes,
        "status": c.status,
        "assigned_to": c.assigned_to,
        "sla_due_at": c.sla_due_at.isoformat() if c.sla_due_at else None,
        "opened_at": c.opened_at.isoformat() if c.opened_at else None,
        "description": c.description,
    }


def _case_detail(db: Session, c: Case) -> dict:
    summary = _case_summary(db, c)
    summary["outcome"] = c.outcome
    summary["rationale"] = c.rationale
    summary["closed_at"] = c.closed_at.isoformat() if c.closed_at else None
    return summary
