"""Integrity router — rule findings, ML anomaly detection, trust ladder."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user, require_role
from ..models import Student, Person, Institution, Case
from ..ml.anomaly_detection import detect_anomalies, run_rules, get_policy_rules, compute_risk_score
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

router = APIRouter(prefix="/integrity", tags=["integrity"])


@router.get("/rules")
def list_rules(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """List all policy rules with their current compliance runway stage."""
    return get_policy_rules()


@router.get("/findings/{institution_id}")
def get_findings(institution_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get all integrity findings for an institution — rule-based + ML."""
    students = db.query(Student).filter(Student.institution_id == institution_id).all()
    records = []
    for s in students:
        person = db.query(Person).filter(Person.id == s.person_id).first()
        records.append({
            "id": s.id,
            "name": person.full_name if person else "Unknown",
            "trust_level": s.trust_level,
            "risk_score": s.risk_score,
            "apaar_id": person.apaar_id if person else None,
            "hold_state": s.hold_state,
            "phone": person.phone if person else None,
        })

    # Run rules
    rule_findings = run_rules(records, institution_id)

    # Run ML anomaly detection
    ml_findings = detect_anomalies(records)

    return {
        "institution_id": institution_id,
        "rule_findings": rule_findings,
        "ml_findings": ml_findings,
        "total_findings": len(rule_findings) + len(ml_findings),
    }


@router.post("/rescore/{institution_id}")
def rescore_students(institution_id: str, db: Session = Depends(get_db),
                     user: dict = Depends(require_role("institution", "officer"))):
    """Recompute risk scores for all students in an institution."""
    students = db.query(Student).filter(Student.institution_id == institution_id).all()
    updated = 0
    for s in students:
        person = db.query(Person).filter(Person.id == s.person_id).first()
        student_data = {
            "hold_state": s.hold_state,
            "trust_level": s.trust_level,
            "apaar_id": person.apaar_id if person else None,
            "risk_factors": [],
        }
        old_score = s.risk_score
        s.risk_score = compute_risk_score(student_data)
        if s.risk_score != old_score:
            updated += 1
    db.commit()
    return {"institution_id": institution_id, "students_checked": len(students), "updated": updated}


@router.get("/trust-distribution")
def trust_dist(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """National trust level distribution."""
    from sqlalchemy import func
    result = {}
    for level in range(5):
        count = db.query(Student).filter(Student.trust_level == level).count()
        result[f"L{level}"] = count
    return result


class BacktestRequest(BaseModel):
    policy_version: int = 7
    compare_version: int = 6


@router.post("/backtest")
def run_backtest(req: BacktestRequest, db: Session = Depends(get_db), user: dict = Depends(require_role("officer"))):
    """Simulate a back-test comparing policy versions (demo)."""
    import random
    old_findings = random.randint(25, 35)
    new_findings = random.randint(35, 45)
    return {
        "policy_version": req.policy_version,
        "compare_version": req.compare_version,
        "old_findings": old_findings,
        "new_findings": new_findings,
        "newly_flagged": max(new_findings - old_findings, 0),
        "reversals": 0,
        "status": "complete",
    }
