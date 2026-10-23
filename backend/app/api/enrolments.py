from fastapi import APIRouter, HTTPException
from typing import Optional
from app.db.state import state
from app.models import HoldToggleRequest, RiskPredictRequest

router = APIRouter(prefix="/api/enrolments", tags=["Enrolments"])

@router.get("")
def get_enrolments(
    search: Optional[str] = None,
    institutionId: Optional[str] = None,
    trustLevel: Optional[int] = None,
    holdState: Optional[str] = None,
    minRisk: Optional[int] = None
):
    res = state.students
    if search:
        s = search.lower()
        res = [
            st for st in res
            if s in st["name"].lower()
            or s in st["maskedId"].lower()
            or s in (st["apaarId"] or "").lower()
            or s in st["programme"].lower()
            or s in st["institutionName"].lower()
        ]
    if institutionId:
        res = [st for st in res if st["institutionId"] == institutionId]
    if trustLevel is not None:
        res = [st for st in res if st["trustLevel"] == trustLevel]
    if holdState and holdState != "ALL":
        res = [st for st in res if st["holdState"] == holdState]
    if minRisk is not None:
        res = [st for st in res if (st.get("riskScore") or 0) >= minRisk]
    return res

@router.get("/{student_id}")
def get_student(student_id: str):
    for st in state.students:
        if st["id"] == student_id:
            return st
    raise HTTPException(status_code=404, detail="Student enrolment record not found")

@router.post("/{student_id}/toggle-hold")
def toggle_student_hold(student_id: str, req: HoldToggleRequest):
    student = None
    for st in state.students:
        if st["id"] == student_id:
            student = st
            break
    if not student:
        raise HTTPException(status_code=404, detail="Student enrolment record not found")

    old_hold = student["holdState"]
    student["holdState"] = req.holdState

    if req.holdState == "NONE":
        student["status"] = "ENROLLED"
        student["trustLevel"] = 3
        is_multi = False
    else:
        student["status"] = "ADMITTED"
        student["trustLevel"] = 1
        is_multi = True

    # Re-evaluate risk with ML model
    age = 18.5
    has_apaar = student.get("apaarId") is not None
    new_risk, factors = state.risk_scorer.evaluate_student(
        age=age,
        submission_days_before_deadline=5.0,
        trust_level=student["trustLevel"],
        has_apaar=has_apaar,
        is_multi_institution_claim=is_multi,
        pool_mismatch=False
    )
    student["riskScore"] = new_risk
    student["riskFactors"] = factors

    # Also resolve any open cases for this student if hold is released
    officer_name = req.officerName or "Shri Rajesh Kumar"
    officer_reason = req.reason or "Officer regulatory hold status adjustment."
    if req.holdState == "NONE":
        for c in state.cases:
            if c.get("subjectId") == student_id and c.get("status") in ["Open", "UnderReview"]:
                c["status"] = "Resolved"
                c["outcome"] = f"Hold released by {officer_name}. Single-seat lock and trust level restored."

    # Append to cryptographic audit chain
    action_type = "HOLD_RELEASED" if req.holdState == "NONE" else "HOLD_APPLIED"
    detail = (
        f"Officer {officer_name} released hold on {student['name']}. Status restored to ENROLLED, Trust Level restored to L{student['trustLevel']}. Reason: {officer_reason}"
        if req.holdState == "NONE"
        else f"Officer {officer_name} applied {req.holdState} on {student['name']}. Status set to ADMITTED, Trust Level set to L1. Reason: {officer_reason}"
    )
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=req.officerName,
        actor_type="officer",
        action=action_type,
        entity="enrolment",
        entity_id=student["id"],
        detail=detail,
        payload={
            "previousHold": old_hold,
            "newHold": req.holdState,
            "status": student["status"],
            "trustLevel": student["trustLevel"],
            "studentRef": student["maskedId"],
            "rationale": req.reason
        }
    )

    return {
        "status": "SUCCESS",
        "student": student,
        "auditBlockSeq": block.seq,
        "message": f"Hold status updated to {req.holdState}."
    }

@router.post("/predict-risk")
def predict_risk(req: RiskPredictRequest):
    """
    Direct ML model inference endpoint for student risk scoring and anomaly detection.
    """
    composite_score, factors = state.risk_scorer.evaluate_student(
        age=req.age,
        submission_days_before_deadline=req.submissionDaysBeforeDeadline,
        trust_level=3 if req.hasApaar else 1,
        has_apaar=req.hasApaar,
        is_multi_institution_claim=req.isMultiInstitutionClaim,
        pool_mismatch=req.poolMismatch,
        category_cert_verified=req.categoryCertVerified
    )

    return {
        "compositeRiskScore": composite_score,
        "riskLevel": "CRITICAL" if composite_score > 60 else "MODERATE" if composite_score > 30 else "LOW",
        "modelType": "IsolationForest Ensemble v2.4",
        "explainableFactors": factors
    }
