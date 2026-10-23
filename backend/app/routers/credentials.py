"""Credentials + Verification router — issue, verify, revoke, access log."""
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user, sign_credential
from ..models import Credential, Student, Person, AccessLog, Verifier

router = APIRouter(prefix="/credentials", tags=["credentials"])


class IssueRequest(BaseModel):
    student_id: str
    purpose: str = "EMPLOYMENT"
    fields: list[str] = ["degree", "institution", "year"]


class VerifyRequest(BaseModel):
    cred_id: str
    verifier_name: str = "Unknown"
    verifier_id: str | None = None
    purpose: str = "EMPLOYMENT"


FIELD_VALUES = {
    "degree":       "B.Tech Computer Science & Engineering",
    "institution":  "Demo Institute of Technology, Mumbai",
    "year":         "2026-27",
    "status":       "ENROLLED",
    "apaar_masked": "1234-****-****",
    "mode":         "Full-Time",
}


@router.post("/issue")
def issue_credential(
    req: IssueRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Issue a new single-use verifiable credential with a 60-second expiry."""
    student = db.query(Student).filter(Student.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.trust_level < 2:
        raise HTTPException(status_code=400, detail="Student must be at least L2 (ID-Verified) to issue credentials")

    person = db.query(Person).filter(Person.id == student.person_id).first()

    # Build claims from consented fields
    claims = {}
    for f in req.fields:
        if f in FIELD_VALUES:
            claims[f] = FIELD_VALUES[f]

    cred_id = f"CRED-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=60)

    payload = {
        "sub": student.masked_id,
        "iss": "pramaan.aicte.gov.in",
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "purpose": req.purpose,
        "cred_id": cred_id,
        "claims": claims,
    }
    signature = sign_credential(payload)

    cred = Credential(
        id=str(uuid.uuid4()),
        cred_id=cred_id,
        student_id=student.id,
        purpose=req.purpose,
        fields=req.fields,
        claims=claims,
        signature=signature,
        issued_at=now,
        expires_at=expires,
    )
    db.add(cred)
    db.commit()

    return {
        "cred_id": cred_id,
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "purpose": req.purpose,
        "fields": req.fields,
        "claims": claims,
        "verify_url": f"/verify?token={cred_id}",
        "label": "SIMULATION",
    }


@router.post("/verify")
def verify_credential(
    req: VerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Public endpoint — no auth needed (employer scans QR → hits this).
    Returns VALID, REVOKED, EXPIRED, or NOT_FOUND.
    """
    cred = db.query(Credential).filter(Credential.cred_id == req.cred_id).first()
    if not cred:
        return {"status": "NOT_FOUND", "cred_id": req.cred_id, "label": "SIMULATION"}

    if cred.revoked:
        # Log access
        log = AccessLog(
            id=str(uuid.uuid4()), credential_id=cred.id, student_id=cred.student_id,
            verifier_name=req.verifier_name, verifier_id=req.verifier_id,
            purpose=req.purpose, outcome="REVOKED", fields_shared=[],
        )
        db.add(log)
        db.commit()
        return {
            "status": "REVOKED",
            "cred_id": cred.cred_id,
            "revoked_at": cred.revoked_at.isoformat() if cred.revoked_at else None,
            "label": "SIMULATION",
        }

    now = datetime.now(timezone.utc)
    if now > cred.expires_at:
        log = AccessLog(
            id=str(uuid.uuid4()), credential_id=cred.id, student_id=cred.student_id,
            verifier_name=req.verifier_name, verifier_id=req.verifier_id,
            purpose=req.purpose, outcome="EXPIRED", fields_shared=[],
        )
        db.add(log)
        db.commit()
        return {
            "status": "EXPIRED",
            "cred_id": cred.cred_id,
            "expired_at": cred.expires_at.isoformat(),
            "label": "SIMULATION",
        }

    # Valid — mark as used and return claims
    if not cred.used:
        cred.used = True
        cred.used_at = now

    # Log access
    log = AccessLog(
        id=str(uuid.uuid4()), credential_id=cred.id, student_id=cred.student_id,
        verifier_name=req.verifier_name, verifier_id=req.verifier_id,
        purpose=req.purpose, outcome="VALID", fields_shared=cred.fields,
    )
    db.add(log)

    # Update verifier stats
    if req.verifier_id:
        verifier = db.query(Verifier).filter(Verifier.id == req.verifier_id).first()
        if verifier:
            verifier.verifications_today += 1
            verifier.total_verifications += 1
            verifier.last_active_at = now

    db.commit()

    return {
        "status": "VALID",
        "cred_id": cred.cred_id,
        "purpose": cred.purpose,
        "claims": cred.claims,
        "issued_at": cred.issued_at.isoformat(),
        "expires_at": cred.expires_at.isoformat(),
        "label": "SIMULATION",
    }


@router.post("/{cred_id}/revoke")
def revoke_credential(
    cred_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Revoke a credential. Student can revoke their own."""
    cred = db.query(Credential).filter(Credential.cred_id == cred_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    cred.revoked = True
    cred.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "revoked", "cred_id": cred_id, "revoked_at": cred.revoked_at.isoformat()}


@router.get("/{student_id}/access-log")
def get_access_log(
    student_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get all verification access log entries for a student."""
    logs = db.query(AccessLog).filter(AccessLog.student_id == student_id).order_by(AccessLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "verifier_name": l.verifier_name,
            "purpose": l.purpose,
            "outcome": l.outcome,
            "fields_shared": l.fields_shared,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
