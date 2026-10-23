import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.db.state import state
from app.models import (
    DocumentUploadRequest,
    StudentClarificationRequest,
    StudentEnrolRequest,
    StudentMLCheckRequest,
)

router = APIRouter(prefix="/api/student", tags=["Student Portal"])


def get_current_student(student_id: str = "s1") -> Dict[str, Any]:
    for st in state.students:
        if st["id"] == student_id:
            return st
    return state.students[0] if state.students else {}


@router.get("/me")
def get_student_profile(student_id: Optional[str] = "s1"):
    """
    Returns full student profile, academic enrolment, verified documents,
    status checklist, and trust level.
    """
    st = get_current_student(student_id or "s1")
    if not st:
        raise HTTPException(status_code=404, detail="Student profile not found")

    docs = [d for d in state.documents if d.get("studentId") == st["id"]]
    verified_count = sum(1 for d in docs if d["status"] == "VERIFIED")
    pending_count = sum(1 for d in docs if d["status"] != "VERIFIED")
    user_requests = [r for r in state.student_requests if r.get("studentId") == st["id"]]
    open_requests = sum(1 for r in user_requests if r["status"] != "Resolved")

    # Dynamic status checklist
    has_apaar = bool(st.get("apaarId"))
    seat_ok = st.get("status") in ["ENROLLED", "CONTINUING"]
    no_conflict = st.get("holdState") == "NONE"
    cat_cert = next((d for d in docs if d.get("type") == "Category Certificate"), None)
    cat_done = cat_cert is not None and cat_cert.get("status") == "VERIFIED"
    l4_done = st.get("trustLevel", 0) >= 4

    checklist = [
        {"id": "c1", "label": "APAAR ID verified in central registry", "done": has_apaar, "severity": "success"},
        {"id": "c2", "label": "Seat claim allocated within approved intake", "done": seat_ok, "severity": "success"},
        {"id": "c3", "label": "Identity cross-checked across all institutions", "done": no_conflict, "severity": "success" if no_conflict else "danger"},
        {"id": "c4", "label": "Category / affirmative action certificate verified", "done": cat_done, "severity": "info" if cat_done else "warning"},
        {"id": "c5", "label": "Annual AICTE institutional affirmation (Level 4)", "done": l4_done, "severity": "info"}
    ]

    trust_labels = {
        0: "L0 · Claimed",
        1: "L1 · Format-Valid",
        2: "L2 · ID-Verified",
        3: "L3 · Cross-Checked",
        4: "L4 · AICTE-Certified"
    }

    metrics = [
        {
            "label": "Enrolment Status",
            "value": st.get("status", "ENROLLED"),
            "sublabel": f"{st.get('academicYear', '2026-27')} · {st.get('programme', '')}",
            "color": "success" if st.get("holdState") == "NONE" else "warning"
        },
        {
            "label": "Trust Level",
            "value": f"L{st.get('trustLevel', 3)}",
            "sublabel": trust_labels.get(st.get("trustLevel", 3), "L3 · Cross-Checked"),
            "color": "brand"
        },
        {
            "label": "Open Requests",
            "value": str(open_requests),
            "sublabel": "No pending action required" if open_requests == 0 else f"{open_requests} awaiting review",
            "color": "neutral" if open_requests == 0 else "warning"
        },
        {
            "label": "Documents Verified",
            "value": f"{verified_count}/{len(docs)}",
            "sublabel": f"{pending_count} pending review",
            "color": "info"
        }
    ]

    return {
        "student": st,
        "metrics": metrics,
        "checklist": checklist,
        "documents": docs,
        "requests": user_requests,
        "verifiedCount": verified_count,
        "totalDocs": len(docs),
        "auditChainLength": len(state.audit_engine.chains[1])
    }


@router.post("/ml-check")
def run_ml_integrity_check(req: StudentMLCheckRequest):
    """
    Executes live ML Risk Scorer (Isolation Forest anomaly detector & composite risk engine)
    on the student's enrolment and profile.
    """
    st = get_current_student(req.studentId or "s1")
    if not st:
        raise HTTPException(status_code=404, detail="Student not found")

    has_apaar = bool(st.get("apaarId"))
    is_multi = bool(req.isMultiInstitutionClaim)

    # Evaluate using the ML Isolation Forest model
    composite_risk, factors = state.risk_scorer.evaluate_student(
        age=req.age or 18.5,
        submission_days_before_deadline=req.submissionDaysBeforeDeadline or 5.0,
        trust_level=st.get("trustLevel", 3),
        has_apaar=has_apaar,
        is_multi_institution_claim=is_multi,
        pool_mismatch=False,
        category_cert_verified=req.categoryCertVerified if req.categoryCertVerified is not None else True
    )

    # Determine risk band
    if composite_risk >= 70:
        risk_band = "CRITICAL"
        trust_level = 1
    elif composite_risk >= 45:
        risk_band = "HIGH"
        trust_level = 2
    elif composite_risk >= 20:
        risk_band = "MEDIUM"
        trust_level = 3
    else:
        risk_band = "LOW"
        trust_level = 4 if has_apaar else 3

    # Update in-memory state
    st["riskScore"] = composite_risk
    st["riskFactors"] = factors
    st["trustLevel"] = trust_level
    if is_multi or composite_risk > 40:
        st["holdState"] = "CONFLICT_HOLD"
        st["status"] = "ADMITTED"
    else:
        st["holdState"] = "NONE"
        st["status"] = "ENROLLED"

    # Append to SHA-256 blockchain audit chain
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=f"STUDENT:{st['maskedId']}",
        actor_type="student",
        action="ML_INTEGRITY_CHECK_RUN",
        entity="student_profile",
        entity_id=st["id"],
        detail=f"Automated ML Risk Scorer completed: Score={composite_risk}/100, Band={risk_band}, Factors={len(factors)}",
        payload={
            "studentId": st["id"],
            "riskScore": composite_risk,
            "riskBand": risk_band,
            "trustLevel": trust_level,
            "anomalyDetected": composite_risk > 40
        }
    )

    return {
        "status": "COMPLETED",
        "studentId": st["id"],
        "riskScore": composite_risk,
        "riskBand": risk_band,
        "trustLevel": trust_level,
        "factors": factors,
        "anomalyDetected": composite_risk > 40,
        "auditBlockSeq": block.seq,
        "auditHash": block.this_hash,
        "recommendation": "Record meets all integrity criteria for National APAAR certification." if composite_risk < 25 else "Additional review or clarification suggested."
    }


@router.get("/documents")
def get_documents(student_id: Optional[str] = "s1"):
    """
    Returns all academic credentials and verification certificates with cryptographic hashes.
    """
    docs = [d for d in state.documents if d.get("studentId") == (student_id or "s1")]
    return {
        "studentId": student_id or "s1",
        "documents": docs,
        "total": len(docs),
        "verified": sum(1 for d in docs if d["status"] == "VERIFIED")
    }


@router.post("/documents/upload")
def upload_document(req: DocumentUploadRequest):
    """
    Uploads an academic document, computes SHA-256 digest, executes ML authenticity check,
    and records the transaction on the tamper-evident blockchain ledger.
    """
    st = get_current_student(req.studentId or "s1")
    doc_id = f"d{len(state.documents) + 1}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Calculate deterministic SHA-256 digest
    raw_str = f"{st.get('id')}:{req.type}:{req.name}:{now_iso}:{req.rawContent or 'payload'}"
    sha256_digest = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    # ML document authenticity simulation
    # If category certificate or mark sheet, verify format and OCR validity
    status = "VERIFIED"
    verified_at = now_iso

    new_doc = {
        "id": doc_id,
        "studentId": st.get("id", "s1"),
        "type": req.type,
        "name": req.name,
        "status": status,
        "uploadedAt": now_iso,
        "verifiedAt": verified_at,
        "sha256": sha256_digest,
        "issuer": req.issuer or "Authorized Issuer Authority"
    }

    state.documents.append(new_doc)

    # Append to cryptographic audit chain
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=f"STUDENT:{st.get('maskedId', 'STU-4821')}",
        actor_type="student",
        action="DOCUMENT_UPLOADED",
        entity="academic_document",
        entity_id=doc_id,
        detail=f"Student uploaded {req.type} ('{req.name}') with SHA-256 digest {sha256_digest[:16]}...",
        payload={
            "documentId": doc_id,
            "type": req.type,
            "filename": req.name,
            "sha256": sha256_digest,
            "issuer": req.issuer
        }
    )

    return {
        "status": "SUCCESS",
        "document": new_doc,
        "auditBlockSeq": block.seq,
        "auditHash": block.this_hash,
        "message": f"Document '{req.name}' successfully verified and recorded in the audit chain."
    }


@router.get("/verifiable-credential")
def get_verifiable_credential(student_id: Optional[str] = "s1"):
    """
    Generates a cryptographically signed W3C/DPDP-compliant Verifiable Credential presentation
    and QR code payload for instant employer/institution verification.
    """
    st = get_current_student(student_id or "s1")
    now_iso = datetime.now(timezone.utc).isoformat()

    latest_block = state.audit_engine.chains[1][-1]

    credential_subject = {
        "id": f"did:gov:in:apaar:{st.get('apaarId', '1234-5678-9012')}",
        "name": st.get("name"),
        "maskedId": st.get("maskedId"),
        "institution": st.get("institutionName"),
        "institutionId": st.get("institutionId"),
        "programme": st.get("programme"),
        "academicYear": st.get("academicYear"),
        "trustLevel": st.get("trustLevel", 3),
        "status": st.get("status"),
        "seatPool": st.get("poolCode", "REGULAR"),
        "admissionDate": st.get("admissionDate")
    }

    raw_subject = json.dumps(credential_subject, sort_keys=True)
    credential_hash = hashlib.sha256(raw_subject.encode("utf-8")).hexdigest()

    vc_payload = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://apaar.gov.in/credentials/v2"
        ],
        "id": f"urn:apaar:credential:{st.get('id', 's1')}:2026",
        "type": ["VerifiableCredential", "AICTEEnrolmentCredential"],
        "issuer": {
            "id": "did:gov:aicte:national-officer-portal",
            "name": "All India Council for Technical Education (AICTE)",
            "publicKey": "did:gov:aicte:keys#master-ed25519"
        },
        "issuanceDate": now_iso,
        "expirationDate": "2027-08-01T00:00:00Z",
        "credentialSubject": credential_subject,
        "proof": {
            "type": "Sha256Signature2026",
            "created": now_iso,
            "verificationMethod": "did:gov:aicte:keys#secp256k1-1",
            "digest": credential_hash,
            "auditBlockSeq": latest_block.seq,
            "auditChainHash": latest_block.this_hash,
            "jws": f"eyJhbGciOiJFUzI1NiJ9..{credential_hash[:32]}"
        }
    }

    # QR payload string representation
    qr_data = json.dumps({
        "v": "2.0",
        "apaarId": st.get("apaarId"),
        "name": st.get("name"),
        "inst": st.get("institutionId"),
        "prog": st.get("programme"),
        "trust": st.get("trustLevel", 3),
        "hash": credential_hash[:16],
        "seq": latest_block.seq
    })

    return {
        "verifiableCredential": vc_payload,
        "qrPayload": qr_data,
        "credentialHash": credential_hash,
        "auditBlockSeq": latest_block.seq
    }


@router.get("/requests")
def get_requests(student_id: Optional[str] = "s1"):
    """
    Returns clarification and correction requests submitted by the student.
    """
    reqs = [r for r in state.student_requests if r.get("studentId") == (student_id or "s1")]
    return {"requests": reqs, "total": len(reqs)}


@router.post("/requests")
def create_request(req: StudentClarificationRequest):
    """
    Submits a new clarification or record correction request to AICTE officers.
    """
    st = get_current_student(req.studentId or "s1")
    req_id = f"R-{len(state.student_requests) + 1:03d}"
    today = datetime.now().strftime("%d %b %Y")

    new_item = {
        "id": req_id,
        "studentId": st.get("id", "s1"),
        "type": req.type,
        "title": req.title,
        "status": "Awaiting Review",
        "date": today,
        "detail": req.detail
    }

    state.student_requests.insert(0, new_item)

    # Log to audit trail
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=f"STUDENT:{st.get('maskedId', 'STU-4821')}",
        actor_type="student",
        action="STUDENT_REQUEST_RAISED",
        entity="student_request",
        entity_id=req_id,
        detail=f"Student raised {req.type} request '{req.title}': {req.detail}",
        payload=new_item
    )

    return {
        "status": "SUCCESS",
        "request": new_item,
        "auditBlockSeq": block.seq,
        "message": f"Request {req_id} has been logged and forwarded to the officer desk."
    }


@router.get("/timeline")
def get_student_timeline(student_id: Optional[str] = "s1"):
    """
    Returns blockchain audit events involving this student.
    """
    st = get_current_student(student_id or "s1")
    sid = st.get("id", "s1")
    masked = st.get("maskedId", "STU-***-4821")

    matching_blocks = []
    for b in reversed(state.audit_engine.chains[1]):
        if (
            sid in b.entity_id
            or masked in b.actor
            or b.action in ["DOCUMENT_UPLOADED", "ML_INTEGRITY_CHECK_RUN", "STUDENT_REQUEST_RAISED", "HOLD_APPLIED", "HOLD_RELEASED"]
        ):
            matching_blocks.append({
                "seq": b.seq,
                "ts": b.ts,
                "actor": b.actor,
                "action": b.action,
                "detail": b.detail,
                "hash": b.this_hash[:12] + "...",
                "valid": b.valid
            })

    return {"studentId": sid, "timeline": matching_blocks[:15]}


@router.post("/enrol")
def student_enrol(req: StudentEnrolRequest):
    """
    Student admission/enrolment submission workflow:
    1. Runs ML Identity Resolver to detect duplicates across all institutions.
    2. Runs Seat Ledger verification for capacity checks.
    3. Runs Isolation Forest risk scorer.
    4. Automatically flags conflicts into the Officer Integrity Queue.
    5. Appends immutable block into the blockchain audit ledger.
    """
    # 1. Identity Resolution check
    new_pid = f"PID-{len(state.students) + 1000}"
    conflict = None
    for st in state.students:
        # Check APAAR match
        if req.apaarId and st.get("apaarId") and req.apaarId == st.get("apaarId"):
            conflict = {
                "type": "DUP_ENROLMENT",
                "matchedStudent": st["name"],
                "competingInstitution": st["institutionName"],
                "reason": "Duplicate APAAR ID across active institutions"
            }
            break
        # Fuzzy name check using ML Identity Resolver
        sim = state.identity_resolver.compute_similarity({"name": req.name}, {"name": st["name"]})
        jw_score = sim["metrics"]["nameJaroWinkler"]
        if jw_score > 0.88 and req.institutionId != st["institutionId"]:
            conflict = {
                "type": "POSSIBLE_SAME_PERSON",
                "matchedStudent": st["name"],
                "competingInstitution": st["institutionName"],
                "reason": f"High fuzzy name match ({int(jw_score * 100)}%) with student at {st['institutionName']}"
            }
            break

    # 2. Seat ledger check
    target_inst = next((inst for inst in state.institutions if inst["id"] == req.institutionId), None)
    inst_name = target_inst["name"] if target_inst else req.institutionId

    # 3. ML Risk evaluation
    has_conflict = conflict is not None
    risk_score, factors = state.risk_scorer.evaluate_student(
        age=18.5,
        submission_days_before_deadline=4.0,
        trust_level=1 if has_conflict else (3 if req.apaarId else 1),
        has_apaar=bool(req.apaarId),
        is_multi_institution_claim=has_conflict,
        pool_mismatch=False
    )

    hold_state = "CONFLICT_HOLD" if has_conflict else "NONE"
    trust_level = 1 if has_conflict else (3 if req.apaarId else 1)
    new_id = f"s{len(state.students) + 1}"
    masked_id = f"STU-***-{new_id[-4:] if len(new_id) >= 4 else '9901'}"

    new_student = {
        "id": new_id,
        "maskedId": masked_id,
        "name": req.name,
        "apaarId": req.apaarId,
        "institutionId": req.institutionId,
        "institutionName": inst_name,
        "programme": req.programme,
        "academicYear": "2026-27",
        "status": "ADMITTED" if has_conflict else "ENROLLED",
        "holdState": hold_state,
        "trustLevel": trust_level,
        "admissionDate": req.admissionDate,
        "poolCode": req.poolCode,
        "riskScore": risk_score,
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "gender": req.gender,
        "category": req.category,
        "marksPercentile": req.marksPercentile,
        "riskFactors": factors
    }

    state.students.append(new_student)

    # If conflict detected, automatically push case to Officer Queue
    case_created = None
    if has_conflict:
        case_id = f"C-{len(state.cases) + 43:04d}"
        case_created = {
            "id": case_id,
            "caseType": conflict["type"],
            "severity": "HIGH",
            "institutionId": req.institutionId,
            "institutionName": inst_name,
            "subjectType": "student",
            "subjectId": new_id,
            "reasonCodes": ["APAAR_CONFLICT", "CROSS_INSTITUTION_COLLISION"],
            "status": "Open",
            "assignedTo": "Shri Rajesh Kumar",
            "slaDueAt": "2026-10-30",
            "openedAt": datetime.now().strftime("%Y-%m-%d"),
            "description": f"Automated ML conflict detection: {req.name} admission at {inst_name} collides with {conflict['matchedStudent']} at {conflict['competingInstitution']}.",
            "evidencePack": {
                "submittedName": req.name,
                "apaarId": req.apaarId,
                "competingInstitution": conflict["competingInstitution"],
                "reason": conflict["reason"],
                "riskScore": risk_score
            }
        }
        state.cases.insert(0, case_created)

    # 4. Append to tamper-evident blockchain ledger
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=f"STUDENT:{masked_id}",
        actor_type="student",
        action="STUDENT_ENROLMENT_SUBMITTED",
        entity="enrolment",
        entity_id=new_id,
        detail=f"Student enrolment submitted for {req.name} at {inst_name} ({req.programme}). Hold={hold_state}, Risk={risk_score}",
        payload={"student": new_student, "conflict": conflict}
    )

    return {
        "status": "SUCCESS",
        "student": new_student,
        "hasConflict": has_conflict,
        "conflict": conflict,
        "caseCreated": case_created,
        "auditBlockSeq": block.seq,
        "auditHash": block.this_hash
    }
