"""Analytics router — dashboard stats, charts, reports for all 3 portals."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import get_db
from ..core.security import get_current_user
from ..models import Student, Institution, Case, SeatPool, Submission, AuditEvent, Person

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """National overview for officer dashboard."""
    total_students = db.query(Student).count()
    total_institutions = db.query(Institution).count()
    open_cases = db.query(Case).filter(~Case.status.in_(["Resolved","Closed"])).count()
    verified = db.query(Student).filter(Student.trust_level >= 2).count()

    return {
        "total_students": total_students,
        "total_institutions": total_institutions,
        "open_cases": open_cases,
        "verified_students": verified,
        "verification_rate": round(verified / total_students * 100, 1) if total_students else 0,
    }


@router.get("/trust-distribution")
def trust_distribution(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Distribution of trust levels across all students."""
    levels = {}
    for l in range(5):
        levels[f"L{l}"] = db.query(Student).filter(Student.trust_level == l).count()
    return levels


@router.get("/enrolment-trend")
def enrolment_trend(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Monthly enrolment vs verification trend."""
    # Based on audit events — for demo, return static structure
    return [
        {"name": "Jun", "enrolled": 820, "verified": 420, "cases": 4},
        {"name": "Jul", "enrolled": 4200, "verified": 2800, "cases": 12},
        {"name": "Aug", "enrolled": 9800, "verified": 7200, "cases": 28},
        {"name": "Sep", "enrolled": 14200, "verified": 11400, "cases": 41},
        {"name": "Oct", "enrolled": 18400, "verified": 15600, "cases": 38},
    ]


@router.get("/cases-by-type")
def cases_by_type(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Count open cases by case type."""
    from collections import Counter
    cases = db.query(Case).filter(~Case.status.in_(["Resolved","Closed"])).all()
    counts = Counter(c.case_type for c in cases)
    return [{"name": k.replace("_"," "), "value": v} for k, v in counts.items()]


@router.get("/region-wise")
def region_wise(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Students by AICTE region."""
    institutions = db.query(Institution).all()
    regions = {}
    for inst in institutions:
        count = db.query(Student).filter(Student.institution_id == inst.id).count()
        regions[inst.region] = regions.get(inst.region, 0) + count
    return [{"name": k, "value": v} for k, v in regions.items()]


@router.get("/institution/{inst_id}")
def institution_analytics(inst_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Analytics for a specific institution dashboard."""
    total = db.query(Student).filter(Student.institution_id == inst_id).count()
    enrolled = db.query(Student).filter(
        Student.institution_id == inst_id,
        Student.status.in_(["ENROLLED","CONTINUING"])
    ).count()
    verified = db.query(Student).filter(
        Student.institution_id == inst_id,
        Student.trust_level >= 2
    ).count()
    on_hold = db.query(Student).filter(
        Student.institution_id == inst_id,
        Student.hold_state != "NONE"
    ).count()
    open_cases = db.query(Case).filter(
        Case.institution_id == inst_id,
        ~Case.status.in_(["Resolved","Closed"])
    ).count()
    submissions = db.query(Submission).filter(Submission.institution_id == inst_id).order_by(Submission.submitted_at.desc()).limit(10).all()

    return {
        "total_students": total,
        "enrolled": enrolled,
        "verified": verified,
        "on_hold": on_hold,
        "open_cases": open_cases,
        "recent_submissions": [
            {
                "batch_id": s.batch_id,
                "submitted_at": s.submitted_at.isoformat(),
                "total_rows": s.total_rows,
                "accepted": s.accepted,
                "rejected": s.rejected,
                "held": s.held,
                "status": s.status,
            }
            for s in submissions
        ],
    }


@router.get("/verifiers")
def list_verifiers(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    from ..models import Verifier
    verifiers = db.query(Verifier).all()
    return [
        {
            "id": v.id, "name": v.name, "verifier_type": v.verifier_type,
            "email": v.email, "status": v.status,
            "purposes_allowed": v.purposes_allowed,
            "quota_daily": v.quota_daily,
            "verifications_today": v.verifications_today,
            "total_verifications": v.total_verifications,
            "registered_at": v.registered_at.isoformat() if v.registered_at else None,
            "last_active_at": v.last_active_at.isoformat() if v.last_active_at else None,
        }
        for v in verifiers
    ]
