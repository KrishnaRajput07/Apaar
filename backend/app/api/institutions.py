from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.db.state import state
from app.models import (
    InstitutionActionRequest,
    InstitutionStudentCreateRequest,
    InstitutionBatchUploadRequest,
    InstitutionFindingResponseRequest,
    InstitutionCaseResponseRequest,
)

router = APIRouter(prefix="/api/institutions", tags=["Institutions"])


def get_inst_or_404(inst_id: str) -> Dict[str, Any]:
    for i in state.institutions:
        if i["id"] == inst_id:
            return i
    raise HTTPException(status_code=404, detail="Institution not found")


@router.get("")
def get_institutions(search: Optional[str] = None, state_filter: Optional[str] = None, band: Optional[str] = None):
    res = state.institutions
    if search:
        s = search.lower()
        res = [i for i in res if s in i["name"].lower() or s in i["id"].lower() or s in i["state"].lower()]
    if state_filter:
        res = [i for i in res if i["state"] == state_filter]
    if band:
        res = [i for i in res if i["integrityBand"] == band]
    return res


@router.get("/{inst_id}")
def get_institution(inst_id: str):
    return get_inst_or_404(inst_id)


@router.post("/{inst_id}/action")
def take_institution_action(inst_id: str, req: InstitutionActionRequest):
    inst = get_inst_or_404(inst_id)

    action_label = {
        "SHOW_CAUSE_NOTICE": "ISSUED_SHOW_CAUSE_NOTICE",
        "FREEZE_ADMISSIONS": "ADMISSION_INTAKE_FROZEN",
        "ORDER_REAUDIT": "REGULATORY_REAUDIT_ORDERED"
    }.get(req.action, req.action)

    detail_str = f"Officer {req.officerName} enforced {req.action} on {inst['name']} ({inst_id}). Reason: {req.reason}"

    # Mutate institution status if intake frozen
    if req.action == "FREEZE_ADMISSIONS":
        inst["status"] = "SUSPENDED"

    # Append to cryptographic audit chain
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=req.officerName,
        actor_type="officer",
        action=action_label,
        entity="institution",
        entity_id=inst_id,
        detail=detail_str,
        payload={"action": req.action, "reason": req.reason, "institution": inst["name"]}
    )

    return {
        "status": "SUCCESS",
        "institution": inst,
        "auditBlockSeq": block.seq,
        "message": f"Action {req.action} successfully enforced and recorded in cryptographic audit ledger."
    }


# ─── 1. Institution Portal Overview ──────────────────────────────────────────
@router.get("/{inst_id}/overview")
def get_institution_overview(inst_id: str):
    inst = get_inst_or_404(inst_id)

    # Students of this institution
    inst_students = [s for s in state.students if s["institutionId"] == inst_id]
    total_records = len(inst_students)
    held_students = sum(1 for s in inst_students if s.get("holdState") != "NONE")
    ready_count = total_records - held_students

    # Cases of this institution
    inst_cases = [c for c in state.cases if c.get("institutionId") == inst_id]
    open_cases = [c for c in inst_cases if c.get("status") not in ["Resolved", "Closed"]]

    # Submissions of this institution
    inst_subs = [s for s in state.submissions if s.get("institutionId") == inst_id]

    # Trust distribution for this institution
    trust_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for s in inst_students:
        lvl = s.get("trustLevel", 3)
        trust_counts[lvl] = trust_counts.get(lvl, 0) + 1

    trust_distribution = [
        {"name": "L4 Certified", "value": trust_counts.get(4, 0), "color": "#6558D3"},
        {"name": "L3 Cross-Checked", "value": trust_counts.get(3, 0), "color": "#198754"},
        {"name": "L2 ID-Verified", "value": trust_counts.get(2, 0), "color": "#2F6FED"},
        {"name": "L1 Format", "value": trust_counts.get(1, 0), "color": "#8791A5"},
        {"name": "L0 Claimed", "value": trust_counts.get(0, 0), "color": "#D0D5E2"},
    ]

    # Seat summary breakdown
    seat_summary = [
        {"pool": "REGULAR", "approved": 240, "claimed": sum(1 for s in inst_students if s.get("poolCode") == "REGULAR"), "status": "OK"},
        {"pool": "NRI", "approved": 36, "claimed": sum(1 for s in inst_students if s.get("poolCode") == "NRI"), "status": "OK"},
        {"pool": "OCI", "approved": 12, "claimed": sum(1 for s in inst_students if s.get("poolCode") == "OCI"), "status": "OK"},
        {"pool": "SUPERNUMERARY", "approved": 12, "claimed": sum(1 for s in inst_students if s.get("poolCode") == "SUPERNUMERARY"), "status": "OK"},
    ]

    metrics = [
        {
            "label": "Total Enrolment Records",
            "value": total_records,
            "sublabel": f"{inst.get('approvedIntake', 240)} approved intake",
            "color": "brand",
            "delta": f"+{total_records} in registry",
            "deltaType": "up"
        },
        {
            "label": "Ready for Submission",
            "value": ready_count,
            "sublabel": f"{held_students} records need attention",
            "color": "success",
            "delta": f"{int((ready_count / max(total_records, 1)) * 100)}% ready rate",
            "deltaType": "neutral"
        },
        {
            "label": "Needs Attention",
            "value": held_students,
            "sublabel": f"{held_students} on regulatory hold",
            "color": "warning" if held_students > 0 else "neutral",
            "delta": "0 unhandled" if held_students == 0 else f"{held_students} held",
            "deltaType": "down" if held_students == 0 else "neutral"
        },
        {
            "label": "Open Cases",
            "value": len(open_cases),
            "sublabel": f"{sum(1 for c in open_cases if c.get('severity') in ['CRITICAL', 'HIGH'])} high priority",
            "color": "danger" if len(open_cases) > 0 else "success",
            "delta": "SLA active",
            "deltaType": "neutral"
        }
    ]

    compliance_trend = [
        {"name": "Jan", "submissions": 12, "errors": 2},
        {"name": "Feb", "submissions": 18, "errors": 3},
        {"name": "Mar", "submissions": 8, "errors": 1},
        {"name": "Aug", "submissions": 142, "errors": 22},
        {"name": "Sep", "submissions": 180, "errors": 5},
        {"name": "Oct", "submissions": total_records, "errors": held_students},
    ]

    return {
        "institution": inst,
        "metrics": metrics,
        "trustDistribution": trust_distribution,
        "seatSummary": seat_summary,
        "openCases": open_cases[:5],
        "recentSubmissions": inst_subs[:5],
        "complianceTrend": compliance_trend,
        "totalStudents": total_records
    }


# ─── 2. Institution Students Roster ──────────────────────────────────────────
@router.get("/{inst_id}/students")
def get_institution_students(
    inst_id: str,
    search: Optional[str] = None,
    programme: Optional[str] = None,
    poolCode: Optional[str] = None,
    status: Optional[str] = None
):
    inst = get_inst_or_404(inst_id)
    res = [s for s in state.students if s["institutionId"] == inst_id]

    if search:
        s = search.lower()
        res = [
            st for st in res
            if s in st["name"].lower()
            or s in st["maskedId"].lower()
            or s in (st.get("apaarId") or "").lower()
            or s in st["programme"].lower()
        ]
    if programme:
        res = [st for st in res if st["programme"] == programme]
    if poolCode:
        res = [st for st in res if st.get("poolCode") == poolCode]
    if status:
        res = [st for st in res if st["status"] == status]

    return res


@router.post("/{inst_id}/students")
def add_institution_student(inst_id: str, req: InstitutionStudentCreateRequest):
    inst = get_inst_or_404(inst_id)

    # 1. Identity Resolution check across ALL institutions
    conflict = None
    for st in state.students:
        # Check APAAR match
        if req.apaarId and st.get("apaarId") and req.apaarId == st.get("apaarId"):
            conflict = {
                "type": "DUP_ENROLMENT",
                "matchedStudent": st["name"],
                "competingInstitution": st["institutionName"],
                "reason": f"Duplicate APAAR ID collision with student at {st['institutionName']}"
            }
            break
        # Fuzzy name check using ML Identity Resolver
        sim = state.identity_resolver.compute_similarity({"name": req.name}, {"name": st["name"]})
        jw_score = sim["metrics"]["nameJaroWinkler"]
        if jw_score > 0.88 and inst_id != st["institutionId"]:
            conflict = {
                "type": "POSSIBLE_SAME_PERSON",
                "matchedStudent": st["name"],
                "competingInstitution": st["institutionName"],
                "reason": f"High fuzzy name match ({int(jw_score * 100)}%) with {st['name']} at {st['institutionName']}"
            }
            break

    # 2. Capacity & ML Risk check
    has_conflict = conflict is not None
    risk_score, factors = state.risk_scorer.evaluate_student(
        age=18.5,
        submission_days_before_deadline=5.0,
        trust_level=1 if has_conflict else (3 if req.apaarId else 1),
        has_apaar=bool(req.apaarId),
        is_multi_institution_claim=has_conflict,
        pool_mismatch=False
    )

    hold_state = "CONFLICT_HOLD" if has_conflict else "NONE"
    status_val = "ADMITTED" if has_conflict else "ENROLLED"
    trust_level = 1 if has_conflict else (3 if req.apaarId else 1)
    new_id = f"s{len(state.students) + 1}"
    masked_id = f"STU-***-{new_id[-4:] if len(new_id) >= 4 else '5512'}"

    new_student = {
        "id": new_id,
        "maskedId": masked_id,
        "name": req.name,
        "apaarId": req.apaarId,
        "institutionId": inst_id,
        "institutionName": inst["name"],
        "programme": req.programme,
        "academicYear": "2026-27",
        "status": status_val,
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
    inst["enrolledCount"] = len([s for s in state.students if s["institutionId"] == inst_id])

    # If conflict detected, automatically push case to Officer Queue
    case_created = None
    if has_conflict:
        case_id = f"C-{len(state.cases) + 43:04d}"
        case_created = {
            "id": case_id,
            "caseType": conflict["type"],
            "severity": "HIGH",
            "institutionId": inst_id,
            "institutionName": inst["name"],
            "subjectType": "student",
            "subjectId": new_id,
            "reasonCodes": ["APAAR_CONFLICT", "CROSS_INSTITUTION_COLLISION"],
            "status": "Open",
            "assignedTo": "Shri Rajesh Kumar",
            "slaDueAt": "2026-10-30",
            "openedAt": datetime.now().strftime("%Y-%m-%d"),
            "description": f"Automated ML conflict detection: {req.name} admission at {inst['name']} collides with {conflict['matchedStudent']} at {conflict['competingInstitution']}.",
            "evidencePack": {
                "submittedName": req.name,
                "apaarId": req.apaarId,
                "competingInstitution": conflict["competingInstitution"],
                "reason": conflict["reason"],
                "riskScore": risk_score
            }
        }
        state.cases.insert(0, case_created)

    # 3. Append to SHA-256 blockchain audit chain
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=f"INSTITUTION:{inst_id}",
        actor_type="institution",
        action="INSTITUTION_STUDENT_ENROLLED",
        entity="student",
        entity_id=new_id,
        detail=f"{inst['name']} enrolled {req.name} in {req.programme} ({req.poolCode}). Hold={hold_state}, Risk={risk_score}",
        payload={"student": new_student, "conflict": conflict}
    )

    return {
        "status": "SUCCESS",
        "student": new_student,
        "hasConflict": has_conflict,
        "conflict": conflict,
        "caseCreated": case_created,
        "auditBlockSeq": block.seq,
        "auditHash": block.this_hash,
        "message": f"Student '{req.name}' successfully registered in {inst['name']} roster."
    }


# ─── 3. Institution Submissions (Batches) ────────────────────────────────────
@router.get("/{inst_id}/submissions")
def get_institution_submissions(inst_id: str):
    return [s for s in state.submissions if s.get("institutionId") == inst_id]


@router.post("/{inst_id}/submissions")
def upload_institution_batch(inst_id: str, req: InstitutionBatchUploadRequest):
    inst = get_inst_or_404(inst_id)
    batch_num = len(state.submissions) + 2902
    batch_id = req.batchId or f"BATCH-{batch_num}"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Synthetic or provided batch processing
    total_rows = len(req.records) if req.records else 245
    rejected = 8
    held = 6
    accepted = total_rows - rejected - held

    submission_item = {
        "id": f"sub{len(state.submissions) + 1}",
        "institutionId": inst_id,
        "institutionName": inst["name"],
        "batchId": batch_id,
        "submittedAt": now_iso,
        "totalRows": total_rows,
        "accepted": accepted,
        "rejected": rejected,
        "held": held,
        "status": "COMPLETED_WITH_ERRORS" if rejected > 0 or held > 0 else "COMPLETED",
        "policyVersion": 7
    }

    if not req.isDryRun:
        state.submissions.insert(0, submission_item)
        inst["lastSubmission"] = datetime.now().strftime("%Y-%m-%d")

        # Record in cryptographic audit ledger
        block = state.audit_engine.append_event(
            chain_id=1,
            actor=f"INSTITUTION:{inst_id}",
            actor_type="institution",
            action="BATCH_ENROLMENT_SUBMITTED",
            entity="batch_submission",
            entity_id=batch_id,
            detail=f"{inst['name']} uploaded batch {batch_id}: {accepted} accepted, {rejected} rejected, {held} held.",
            payload=submission_item
        )
        audit_seq = block.seq
    else:
        audit_seq = state.audit_engine.chains[1][-1].seq

    return {
        "status": "SUCCESS",
        "isDryRun": req.isDryRun,
        "batch": submission_item,
        "auditBlockSeq": audit_seq,
        "errors": [
            {"row": 14, "apaarId": "INVALID_FORMAT", "reason": "APAAR ID must contain exactly 12 digits"},
            {"row": 42, "studentId": "DUPLICATE_ROW", "reason": "Student ID repeated multiple times in batch"},
            {"row": 89, "programme": "INTAKE_CAP", "reason": "B.Tech CSE REGULAR pool exceeded cap"}
        ],
        "message": f"Batch {batch_id} validated successfully."
    }


# ─── 4. Institution Integrity Findings ───────────────────────────────────────
@router.get("/{inst_id}/integrity")
def get_institution_integrity(inst_id: str):
    inst = get_inst_or_404(inst_id)
    checks = [c for c in state.integrity_checks if c.get("institutionId") == inst_id]
    open_count = sum(1 for c in checks if c.get("status") == "OPEN")
    resolved_count = sum(1 for c in checks if c.get("status") == "RESOLVED")

    # Seat ledger breakdown
    inst_students = [s for s in state.students if s["institutionId"] == inst_id]
    cse_claimed = sum(1 for s in inst_students if "CSE" in s.get("programme", "") and s.get("poolCode") == "REGULAR")
    ece_claimed = sum(1 for s in inst_students if "ECE" in s.get("programme", "") and s.get("poolCode") == "REGULAR")
    mech_claimed = sum(1 for s in inst_students if "Mech" in s.get("programme", "") and s.get("poolCode") == "REGULAR")

    seat_ledger = [
        {"programme": "B.Tech CSE", "poolCode": "REGULAR", "approved": 60, "claimed": max(cse_claimed, 62), "status": "BREACH"},
        {"programme": "B.Tech ECE", "poolCode": "REGULAR", "approved": 60, "claimed": max(ece_claimed, 58), "status": "OK"},
        {"programme": "B.Tech Mech", "poolCode": "REGULAR", "approved": 60, "claimed": max(mech_claimed, 55), "status": "OK"},
        {"programme": "M.Tech AI", "poolCode": "REGULAR", "approved": 30, "claimed": 28, "status": "OK"},
        {"programme": "B.Tech CSE", "poolCode": "NRI", "approved": 9, "claimed": 11, "status": "BREACH"},
        {"programme": "B.Tech ECE", "poolCode": "OCI", "approved": 3, "claimed": 2, "status": "OK"},
        {"programme": "B.Tech Mech", "poolCode": "SUPERNUMERARY", "approved": 3, "claimed": 5, "status": "WARNING"},
    ]

    return {
        "checks": checks,
        "openCount": open_count,
        "resolvedCount": resolved_count,
        "seatLedger": seat_ledger
    }


@router.post("/{inst_id}/integrity/{finding_id}/respond")
def respond_institution_finding(inst_id: str, finding_id: str, req: InstitutionFindingResponseRequest):
    target = None
    for c in state.integrity_checks:
        if c.get("id") == finding_id and c.get("institutionId") == inst_id:
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Integrity finding not found")

    target["status"] = "RESOLVED"
    target["response"] = req.response

    block = state.audit_engine.append_event(
        chain_id=1,
        actor=req.officerOrAdminName or f"INSTITUTION:{inst_id}",
        actor_type="institution",
        action="INTEGRITY_FINDING_RESPONDED",
        entity="integrity_check",
        entity_id=finding_id,
        detail=f"Institution responded to {finding_id} ({target['rule']}): {req.response}",
        payload={"findingId": finding_id, "response": req.response}
    )

    return {
        "status": "SUCCESS",
        "finding": target,
        "auditBlockSeq": block.seq,
        "message": f"Response recorded for finding {finding_id}."
    }


# ─── 5. Institution Cases ────────────────────────────────────────────────────
@router.get("/{inst_id}/cases")
def get_institution_cases(inst_id: str):
    return [c for c in state.cases if c.get("institutionId") == inst_id]


@router.post("/{inst_id}/cases/{case_id}/respond")
def respond_institution_case(inst_id: str, case_id: str, req: InstitutionCaseResponseRequest):
    target = None
    for c in state.cases:
        if c.get("id") == case_id and c.get("institutionId") == inst_id:
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Case not found")

    target["status"] = "UnderReview"
    target["institutionResponse"] = {
        "response": req.response,
        "evidenceSummary": req.evidenceSummary,
        "submittedBy": req.adminName,
        "submittedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    block = state.audit_engine.append_event(
        chain_id=1,
        actor=req.adminName or f"INSTITUTION:{inst_id}",
        actor_type="institution",
        action="CASE_RESPONSE_SUBMITTED",
        entity="case",
        entity_id=case_id,
        detail=f"Institution admin {req.adminName} submitted response on Case {case_id}: {req.response}",
        payload={"caseId": case_id, "response": req.response, "evidence": req.evidenceSummary}
    )

    return {
        "status": "SUCCESS",
        "case": target,
        "auditBlockSeq": block.seq,
        "message": f"Response for Case {case_id} submitted to AICTE officer review desk."
    }
