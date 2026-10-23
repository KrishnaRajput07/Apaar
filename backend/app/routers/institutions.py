"""Institutions router — list, detail, create, seat pools."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user, require_role
from ..models import Institution, SeatPool, Case, Submission

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/")
def list_institutions(
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    insts = db.query(Institution).offset(skip).limit(limit).all()
    return [_inst_summary(db, i) for i in insts]


@router.get("/{inst_id}")
def get_institution(inst_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    inst = db.query(Institution).filter(Institution.id == inst_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return _inst_detail(db, inst)


@router.get("/{inst_id}/seats")
def get_seat_pools(inst_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    pools = db.query(SeatPool).filter(SeatPool.institution_id == inst_id).all()
    return [
        {
            "id": p.id, "programme": p.programme, "pool_code": p.pool_code,
            "academic_year": p.academic_year,
            "approved": p.approved_intake, "claimed": p.claimed,
            "remaining": p.approved_intake - p.claimed,
            "status": p.status,
        }
        for p in pools
    ]


@router.post("/{inst_id}/seats")
def create_seat_pool(inst_id: str, pool: dict, db: Session = Depends(get_db),
                     user: dict = Depends(require_role("institution", "officer"))):
    import uuid
    new_pool = SeatPool(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        programme=pool["programme"],
        pool_code=pool["pool_code"],
        academic_year=pool.get("academic_year", "2026-27"),
        approved_intake=pool["approved_intake"],
        claimed=0, status="OK",
    )
    db.add(new_pool)
    db.commit()
    db.refresh(new_pool)
    return {"id": new_pool.id, "status": "created"}


def _inst_summary(db: Session, inst: Institution) -> dict:
    student_count = db.query(db.query(__import__("..models", fromlist=["Student"]).Student).filter(__import__("..models", fromlist=["Student"]).Student.institution_id == inst.id).statement).count()
    # Simpler: just count directly
    from ..models import Student
    enrolled = db.query(Student).filter(Student.institution_id == inst.id, Student.status.in_(["ENROLLED","CONTINUING"])).count()
    verified = db.query(Student).filter(Student.institution_id == inst.id, Student.trust_level >= 2).count()
    open_cases = db.query(Case).filter(Case.institution_id == inst.id, ~Case.status.in_(["Resolved","Closed"])).count()
    return {
        "id": inst.id, "name": inst.name, "aicte_code": inst.aicte_code,
        "state": inst.state, "district": inst.district, "region": inst.region,
        "type": inst.inst_type, "status": inst.status,
        "integrity_band": inst.integrity_band, "integrity_score": inst.integrity_score,
        "enrolled_count": enrolled, "verified_count": verified,
        "open_cases": open_cases,
        "last_submission": inst.last_submission.isoformat() if inst.last_submission else None,
    }


def _inst_detail(db: Session, inst: Institution) -> dict:
    summary = _inst_summary(db, inst)
    pools = db.query(SeatPool).filter(SeatPool.institution_id == inst.id).all()
    summary["seat_pools"] = [
        {"programme": p.programme, "pool_code": p.pool_code, "approved": p.approved_intake, "claimed": p.claimed, "status": p.status}
        for p in pools
    ]
    return summary
