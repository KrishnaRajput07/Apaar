from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timezone
from app.db.state import state
from app.models import VerifierStatusRequest, VerifierQuotaRequest, VerifySimulationRequest

router = APIRouter(prefix="/api/verifier", tags=["Verifier Portal"])

@router.get("/list")
def get_verifiers(search: Optional[str] = None):
    res = state.verifiers
    if search:
        s = search.lower()
        res = [v for v in res if s in v["name"].lower() or s in v["type"].lower() or s in v["email"].lower()]
    return res

@router.get("/logs")
def get_verification_logs():
    return state.verification_logs

@router.post("/{verifier_id}/status")
def update_verifier_status(verifier_id: str, req: VerifierStatusRequest):
    v = next((x for x in state.verifiers if x["id"] == verifier_id), None)
    if not v:
        raise HTTPException(status_code=404, detail="Verifier not found")

    old_status = v["status"]
    v["status"] = req.status
    if req.status == "ACTIVE" and old_status == "PENDING" and v["quotaDaily"] == 0:
        v["quotaDaily"] = 50

    # Log to cryptographic audit chain
    block = state.audit_engine.append_event(
        chain_id=3,
        actor=req.officerName,
        actor_type="officer",
        action="VERIFIER_STATUS_CHANGED",
        entity="verifier",
        entity_id=verifier_id,
        detail=f"Officer {req.officerName} updated status of verifier {v['name']} ({verifier_id}) from {old_status} to {req.status}.",
        payload={"verifierId": verifier_id, "oldStatus": old_status, "newStatus": req.status}
    )

    return {
        "status": "SUCCESS",
        "verifier": v,
        "auditBlockSeq": block.seq,
        "message": f"Verifier status set to {req.status}."
    }

@router.post("/{verifier_id}/quota")
def update_verifier_quota(verifier_id: str, req: VerifierQuotaRequest):
    v = next((x for x in state.verifiers if x["id"] == verifier_id), None)
    if not v:
        raise HTTPException(status_code=404, detail="Verifier not found")

    old_quota = v["quotaDaily"]
    v["quotaDaily"] = req.quotaDaily

    return {
        "status": "SUCCESS",
        "verifier": v,
        "message": f"Daily verification quota updated from {old_quota} to {req.quotaDaily}."
    }

@router.post("/simulate-verify")
def simulate_verification(req: VerifySimulationRequest):
    """
    Executes a real simulation of a third-party verifier querying student credentials.
    Checks verifier status, daily quota, consent reference, and returns selective disclosure.
    """
    v = next((x for x in state.verifiers if x["id"] == req.verifierId), None)
    if not v:
        raise HTTPException(status_code=404, detail="Verifier not registered in AICTE ecosystem.")

    if v["status"] != "ACTIVE":
        raise HTTPException(status_code=403, detail=f"Verifier {v['name']} is currently {v['status']}. Verification requests denied.")

    if v["verificationsToday"] >= v["quotaDaily"]:
        raise HTTPException(status_code=429, detail=f"Verifier daily quota exhausted ({v['verificationsToday']}/{v['quotaDaily']}). Request quota enhancement.")

    # Match student
    student = next(
        (st for st in state.students if req.studentRef.lower() in st["maskedId"].lower() or (st["apaarId"] and req.studentRef in st["apaarId"])),
        None
    )

    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not student:
        log_entry = {
            "id": f"VL-00{len(state.verification_logs) + 1}",
            "verifierId": v["id"],
            "verifierName": v["name"],
            "purpose": req.purpose,
            "outcome": "NOT_FOUND",
            "fieldsReturned": [],
            "at": now_ts,
            "consentRef": req.consentRef
        }
        state.verification_logs.insert(0, log_entry)
        return {"outcome": "NOT_FOUND", "message": "No matching student credential located in AICTE registry.", "log": log_entry}

    # Check revoked consent simulation
    if "7810" in req.consentRef or student["id"] == "s5":
        log_entry = {
            "id": f"VL-00{len(state.verification_logs) + 1}",
            "verifierId": v["id"],
            "verifierName": v["name"],
            "purpose": req.purpose,
            "outcome": "REVOKED",
            "fieldsReturned": [],
            "at": now_ts,
            "consentRef": req.consentRef
        }
        state.verification_logs.insert(0, log_entry)
        return {"outcome": "REVOKED", "message": "Student has revoked consent for this verification request.", "log": log_entry}

    # Successful verification with selective disclosure based on purpose
    disclosed_fields = ["degree", "programme", "institution", "academicYear", "enrolmentStatus"]
    if req.purpose == "EMPLOYMENT":
        disclosed_fields.append("trustLevel")
    elif req.purpose == "SCHOLARSHIP":
        disclosed_fields.append("marksPercentile")

    v["verificationsToday"] += 1
    v["totalVerifications"] += 1
    v["lastActive"] = now_ts[:10]

    log_entry = {
        "id": f"VL-00{len(state.verification_logs) + 1}",
        "verifierId": v["id"],
        "verifierName": v["name"],
        "purpose": req.purpose,
        "outcome": "VALID",
        "fieldsReturned": disclosed_fields,
        "at": now_ts,
        "consentRef": req.consentRef
    }
    state.verification_logs.insert(0, log_entry)

    # Append to cryptographic audit chain
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=v["name"],
        actor_type="institution",
        action="CREDENTIAL_VERIFIED_BY_THIRD_PARTY",
        entity="credential",
        entity_id=student["id"],
        detail=f"Verifier {v['name']} verified student {student['maskedId']} for {req.purpose}. Consent Ref: {req.consentRef}.",
        payload={"verifier": v["name"], "studentRef": student["maskedId"], "purpose": req.purpose, "fields": disclosed_fields}
    )

    return {
        "outcome": "VALID",
        "verifiedStudent": {
            "maskedId": student["maskedId"],
            "name": student["name"],
            "institutionName": student["institutionName"],
            "programme": student["programme"],
            "academicYear": student["academicYear"],
            "trustLevel": student["trustLevel"],
            "status": student["status"],
            "disclosedFields": disclosed_fields
        },
        "verifierQuotaRemaining": v["quotaDaily"] - v["verificationsToday"],
        "logEntry": log_entry,
        "auditBlockSeq": block.seq
    }
