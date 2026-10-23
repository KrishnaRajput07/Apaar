"""Students router — list, detail, upload batch, claim seat."""
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core.database import get_db
from ..core.security import get_current_user, require_role
from ..models import Student, Person, Institution, SeatPool, SeatClaim, Submission, Case
from ..adapters.apaar_mock import verify_apaar, generate_apaar_id, generate_ppid, seed_known_apaar

router = APIRouter(prefix="/students", tags=["students"])


class EnrolmentRow(BaseModel):
    name: str
    apaar_id: str | None = None
    dob: str | None = None
    gender: str | None = None
    programme: str
    pool_code: str = "REGULAR"
    admission_date: str | None = None


class BatchUploadRequest(BaseModel):
    institution_id: str
    rows: list[EnrolmentRow]
    dry_run: bool = False
    idempotency_key: str | None = None


@router.get("/")
def list_students(
    institution_id: str | None = None,
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(Student)
    if institution_id:
        q = q.filter(Student.institution_id == institution_id)
    students = q.offset(skip).limit(limit).all()
    return [_student_summary(db, s) for s in students]


@router.get("/{student_id}")
def get_student(student_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return _student_detail(db, s)


@router.post("/upload-batch")
def upload_batch(
    req: BatchUploadRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("institution", "officer")),
):
    """
    Ingestion pipeline: S0 auth → S1 schema → S2/S4 APAAR → S5 seat claim → S6 lock → S8 trust.
    Returns per-row results + a signed receipt.
    """
    results = []
    accepted = 0
    rejected = 0
    held = 0
    errors = []

    # Idempotency
    idem_key = req.idempotency_key or f"batch-{uuid.uuid4()}"
    existing = db.query(Submission).filter(Submission.idempotency_key == idem_key).first()
    if existing:
        return {"status": "duplicate", "batch_id": existing.batch_id, "message": "Batch already processed"}

    batch_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"

    for i, row in enumerate(req.rows):
        row_errors = []

        # S1: Schema check
        if not row.name:
            row_errors.append("MISSING_NAME")
        if not row.programme:
            row_errors.append("MISSING_PROGRAMME")

        # S2/S4: APAAR verification
        person = None
        if row.apaar_id:
            result = verify_apaar(row.apaar_id, row.name, row.dob or "")
            if not result.verified:
                if result.error == "APAAR_ID_NOT_FOUND":
                    row_errors.append("INVALID_APAAR")
                elif result.name_match < 0.85:
                    row_errors.append(f"NAME_MISMATCH:{result.name_match}")
                if not result.dob_match:
                    row_errors.append("DOB_MISMATCH")
            # Find or create person
            person = db.query(Person).filter(Person.apaar_id == row.apaar_id).first()
            if not person and not row_errors:
                person = Person(
                    id=str(uuid.uuid4()),
                    full_name=row.name, apaar_id=row.apaar_id,
                    dob=row.dob, gender=row.gender,
                    trust_level=1,
                )
                db.add(person)
                db.flush()
                seed_known_apaar(row.apaar_id, row.name, row.dob or "", "photo_hash")
        else:
            # No APAAR → provisional identity (PPID)
            ppid = generate_ppid()
            person = Person(
                id=str(uuid.uuid4()),
                full_name=row.name, ppid=ppid,
                dob=row.dob, gender=row.gender,
                trust_level=0,
            )
            db.add(person)
            db.flush()

        if row_errors:
            rejected += 1
            errors.append({"row": i, "name": row.name, "errors": row_errors})
            results.append({"row": i, "status": "rejected", "errors": row_errors})
            continue

        # S5: Seat claim
        pool = db.query(SeatPool).filter(
            SeatPool.institution_id == req.institution_id,
            SeatPool.programme == row.programme,
            SeatPool.pool_code == row.pool_code,
            SeatPool.academic_year == "2026-27",
        ).first()

        if not pool:
            row_errors.append("POOL_NOT_FOUND")
            rejected += 1
            errors.append({"row": i, "name": row.name, "errors": row_errors})
            results.append({"row": i, "status": "rejected", "errors": row_errors})
            continue

        if req.dry_run:
            accepted += 1
            results.append({"row": i, "status": "dry_run", "name": row.name, "pool": pool.pool_code})
            continue

        # Call claim_seat SQL function
        claim_result = db.execute(
            text("SELECT * FROM claim_seat(:pid, :sid)"),
            {"pid": pool.id, "sid": "dry-run"}
        ).fetchone()

        if claim_result:
            slot_no, over_by, cap, pool_status = claim_result

            # S6: Single-Seat Lock (check for existing active enrolment)
            existing_enrolment = db.query(Student).filter(
                Student.person_id == person.id,
                Student.status.in_(["ENROLLED", "CONTINUING", "ADMITTED"]),
                Student.institution_id != req.institution_id,
            ).first()

            hold_state = "NONE"
            if existing_enrolment:
                hold_state = "CONFLICT_HOLD"
                held += 1
            elif over_by > 0:
                held += 1

            # Create student record
            student = Student(
                id=f"STU-{uuid.uuid4().hex[:8].upper()}",
                masked_id=f"STU-***-{random.randint(1000,9999)}",
                person_id=person.id,
                institution_id=req.institution_id,
                programme=row.programme,
                academic_year="2026-27",
                pool_code=row.pool_code,
                status="CONFLICT_HOLD" if hold_state == "CONFLICT_HOLD" else "ENROLLED",
                hold_state=hold_state,
                trust_level=person.trust_level,
                risk_score=0,
                admission_date=row.admission_date or "2026-08-01",
                batch_id=batch_id,
            )
            db.add(student)
            db.flush()

            # Create seat claim
            claim = SeatClaim(
                id=str(uuid.uuid4()),
                pool_id=pool.id,
                student_id=student.id,
                slot_no=slot_no,
                over_by=over_by,
            )
            db.add(claim)

            # Open case if breach or conflict
            if over_by > 0 or hold_state == "CONFLICT_HOLD":
                case = Case(
                    id=f"CASE-{uuid.uuid4().hex[:8].upper()}",
                    case_ref=f"C-{uuid.uuid4().hex[:6].upper()}",
                    case_type="INTAKE_BREACH" if over_by > 0 else "DUP_ENROLMENT",
                    severity="HIGH",
                    institution_id=req.institution_id,
                    subject_type="student",
                    subject_id=student.id,
                    reason_codes=["POOL_OVER_CAP"] if over_by > 0 else ["LOCK_VIOLATION","APAAR_CONFLICT"],
                    description=f"{'Pool over cap by ' + str(over_by) if over_by > 0 else 'Active enrolment conflict'} for {row.name}",
                    status="Open",
                    sla_due_at=datetime.now(timezone.utc) + timedelta(days=7),
                )
                db.add(case)

            accepted += 1
            results.append({
                "row": i, "status": "accepted", "name": row.name,
                "slot_no": slot_no, "over_by": over_by,
                "trust_level": person.trust_level,
            })
        else:
            rejected += 1
            row_errors.append("SEAT_CLAIM_FAILED")
            errors.append({"row": i, "name": row.name, "errors": row_errors})

    # Create submission record
    if not req.dry_run:
        submission = Submission(
            id=str(uuid.uuid4()),
            institution_id=req.institution_id,
            batch_id=batch_id,
            idempotency_key=idem_key,
            total_rows=len(req.rows),
            accepted=accepted,
            rejected=rejected,
            held=held,
            status="COMPLETED_WITH_ERRORS" if rejected > 0 else "COMPLETED",
            policy_version=7,
            error_report={"errors": errors} if errors else None,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(submission)

        # Update institution last_submission
        inst = db.query(Institution).filter(Institution.id == req.institution_id).first()
        if inst:
            inst.last_submission = datetime.now(timezone.utc)

    db.commit()

    return {
        "batch_id": batch_id,
        "total_rows": len(req.rows),
        "accepted": accepted,
        "rejected": rejected,
        "held": held,
        "dry_run": req.dry_run,
        "results": results,
        "errors": errors if errors else None,
        "signed_receipt": f"RCPT-{batch_id}-{uuid.uuid4().hex[:8].upper()}",
        "policy_version": 7,
    }


@router.get("/institution/{inst_id}/submissions")
def list_submissions(inst_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    subs = db.query(Submission).filter(Submission.institution_id == inst_id).order_by(Submission.submitted_at.desc()).limit(20).all()
    return [
        {
            "id": s.id, "batch_id": s.batch_id,
            "submitted_at": s.submitted_at.isoformat(),
            "total_rows": s.total_rows, "accepted": s.accepted,
            "rejected": s.rejected, "held": s.held,
            "status": s.status, "policy_version": s.policy_version,
        }
        for s in subs
    ]


import random  # needed for masked_id generation

def _student_summary(db: Session, s: Student) -> dict:
    person = db.query(Person).filter(Person.id == s.person_id).first()
    inst = db.query(Institution).filter(Institution.id == s.institution_id).first()
    return {
        "id": s.id, "masked_id": s.masked_id,
        "name": person.full_name if person else "Unknown",
        "apaar_id": person.apaar_id if person else None,
        "institution_id": s.institution_id,
        "institution_name": inst.name if inst else "",
        "programme": s.programme, "academic_year": s.academic_year,
        "status": s.status, "hold_state": s.hold_state,
        "trust_level": s.trust_level, "risk_score": s.risk_score,
        "pool_code": s.pool_code,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _student_detail(db: Session, s: Student) -> dict:
    summary = _student_summary(db, s)
    person = db.query(Person).filter(Person.id == s.person_id).first()
    summary["person"] = {
        "id": person.id if person else None,
        "full_name": person.full_name if person else None,
        "dob": person.dob if person else None,
        "gender": person.gender if person else None,
        "phone": person.phone if person else None,
        "apaar_id": person.apaar_id if person else None,
        "ppid": person.ppid if person else None,
    } if person else None
    claim = db.query(SeatClaim).filter(SeatClaim.student_id == s.id).first()
    summary["seat_claim"] = {
        "slot_no": claim.slot_no, "over_by": claim.over_by,
    } if claim else None
    return summary
