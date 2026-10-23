"""Seats router — national seat ledger, pool breakdown, breach detection."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import get_db
from ..core.security import get_current_user
from ..models import Institution, SeatPool, SeatClaim, Student

router = APIRouter(prefix="/seats", tags=["seats"])


@router.get("/national")
def national_seat_ledger(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """National summary across all institutions."""
    institutions = db.query(Institution).all()
    total_approved = 0
    total_enrolled = 0
    breaches = []

    for inst in institutions:
        pools = db.query(SeatPool).filter(SeatPool.institution_id == inst.id).all()
        for p in pools:
            total_approved += p.approved_intake
            total_enrolled += p.claimed
            if p.claimed > p.approved_intake:
                breaches.append({
                    "institution_id": inst.id,
                    "institution_name": inst.name,
                    "programme": p.programme,
                    "pool_code": p.pool_code,
                    "approved": p.approved_intake,
                    "claimed": p.claimed,
                    "over_by": p.claimed - p.approved_intake,
                })

    return {
        "total_approved": total_approved,
        "total_enrolled": total_enrolled,
        "total_remaining": max(total_approved - total_enrolled, 0),
        "utilisation_pct": round(total_enrolled / total_approved * 100, 1) if total_approved else 0,
        "breach_count": len(breaches),
        "breaches": breaches,
    }


@router.get("/institution/{inst_id}")
def institution_seats(inst_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Pool-level breakdown for a specific institution."""
    pools = db.query(SeatPool).filter(SeatPool.institution_id == inst_id).all()
    return [
        {
            "id": p.id,
            "programme": p.programme,
            "pool_code": p.pool_code,
            "academic_year": p.academic_year,
            "approved": p.approved_intake,
            "claimed": p.claimed,
            "remaining": p.approved_intake - p.claimed,
            "over_by": max(p.claimed - p.approved_intake, 0),
            "status": p.status,
        }
        for p in pools
    ]


@router.get("/all-institutions")
def all_institution_seats(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Per-institution seat summary for the officer dashboard."""
    institutions = db.query(Institution).all()
    result = []
    for inst in institutions:
        pools = db.query(SeatPool).filter(SeatPool.institution_id == inst.id).all()
        approved = sum(p.approved_intake for p in pools)
        enrolled = sum(p.claimed for p in pools)
        verified = db.query(Student).filter(
            Student.institution_id == inst.id,
            Student.trust_level >= 2
        ).count()
        breach = any(p.claimed > p.approved_intake for p in pools)
        result.append({
            "id": inst.id,
            "name": inst.name,
            "state": inst.state,
            "approved": approved,
            "enrolled": enrolled,
            "verified": verified,
            "util_pct": round(enrolled / approved * 100, 1) if approved else 0,
            "breach": breach,
            "status": "BREACH" if breach else "NEAR CAP" if enrolled / approved > 0.95 if approved else False else "OK",
        })
    return result
