from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timezone
from app.db.state import state
from app.models import OfficerDecisionRequest

router = APIRouter(prefix="/api/queue", tags=["Integrity Queue"])

@router.get("")
def get_queue(filter_mode: Optional[str] = "all"):
    cases = state.cases
    if filter_mode == "open":
        return [c for c in cases if c["status"] not in ["Resolved", "Closed"]]
    elif filter_mode == "critical":
        return [c for c in cases if c["severity"] in ["CRITICAL", "HIGH"]]
    elif filter_mode == "awaiting":
        return [c for c in cases if c["status"] == "AwaitingInstitution"]
    return cases

@router.get("/{case_id}")
def get_case(case_id: str):
    for c in state.cases:
        if c["id"] == case_id:
            return c
    raise HTTPException(status_code=404, detail="Case not found")

@router.post("/{case_id}/decision")
def record_officer_decision(case_id: str, req: OfficerDecisionRequest):
    if not req.rationale.strip():
        raise HTTPException(status_code=400, detail="Mandatory officer rationale required for regulatory compliance.")

    target_case = None
    for c in state.cases:
        if c["id"] == case_id:
            target_case = c
            break

    if not target_case:
        raise HTTPException(status_code=404, detail="Case not found")

    decision_outcomes = {
        "RESOLVE_NO_ISSUE": ("Resolved", "Resolved — evidence verified, no regulatory breach detected."),
        "UPHOLD_BREACH": ("Resolved", "Upheld — breach affirmed. Remediation order issued to institution."),
        "REQUEST_CLARIFICATION": ("AwaitingInstitution", "Awaiting Institution — official inquiry notice dispatched with 7-day SLA."),
        "ESCALATE_COMMITTEE": ("Escalated", "Escalated — forwarded to AICTE National Regulatory Appeals Committee."),
        "ENFORCE_PENALTY": ("Resolved", "Penalty Enforced — regulatory fine and admission reduction applied.")
    }

    new_status, outcome_text = decision_outcomes.get(req.decision, ("UnderReview", req.decision))
    
    target_case["status"] = new_status
    target_case["outcome"] = f"{outcome_text} Rationale: {req.rationale}"
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if new_status in ["Resolved", "Closed"]:
        target_case["closedAt"] = now_ts

    # Synchronize student state if case was raised on a student
    if target_case.get("subjectType") == "student" and target_case.get("subjectId"):
        for st in state.students:
            if st["id"] == target_case["subjectId"]:
                if req.decision == "RESOLVE_NO_ISSUE":
                    st["holdState"] = "NONE"
                    st["status"] = "ENROLLED"
                    st["trustLevel"] = 3
                    st["riskScore"] = 10
                    st["riskFactors"] = [
                        {"factor": "Resolved by Officer Mediation", "impact": "-35 pts", "severity": "INFO", "detail": f"Case {case_id} adjudicated by {req.officerName}."}
                    ]
                elif req.decision in ["UPHOLD_BREACH", "ENFORCE_PENALTY"]:
                    st["holdState"] = "CONFLICT_HOLD"
                    st["status"] = "CANCELLED"
                    st["trustLevel"] = 1

    # Append immutable event to Cryptographic Audit Hash Chain
    audit_block = state.audit_engine.append_event(
        chain_id=1,
        actor=req.officerName,
        actor_type="officer",
        action="CASE_DECISION_RECORDED",
        entity="case",
        entity_id=case_id,
        detail=f"Officer {req.officerName} rendered decision '{req.decision}' on Case {case_id} ({target_case['caseType']}). Outcome: {new_status}.",
        payload={
            "caseId": case_id,
            "decision": req.decision,
            "status": new_status,
            "rationale": req.rationale,
            "institution": target_case["institutionName"]
        }
    )

    return {
        "status": "SUCCESS",
        "case": target_case,
        "auditBlock": audit_block.to_dict(),
        "message": f"Officer decision registered successfully in Case {case_id} and permanently anchored in the audit chain."
    }
