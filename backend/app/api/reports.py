import io
import csv
import json
from fastapi import APIRouter, HTTPException, Response
from app.db.state import state

router = APIRouter(prefix="/api/reports", tags=["Reports"])

REPORT_METADATA = [
    {
        "id": "national-enrolment-summary",
        "name": "National Enrolment Summary",
        "desc": "Aggregate enrolment across all institutions by programme, state and pool — AY 2026-27",
        "updated": "21 Oct 2026",
        "format": "CSV",
        "filename": "AICTE_National_Enrolment_Summary_AY2026-27.csv"
    },
    {
        "id": "integrity-risk-report",
        "name": "Integrity Risk Report",
        "desc": "Open cases, breach institutions, integrity index distribution",
        "updated": "21 Oct 2026",
        "format": "CSV",
        "filename": "AICTE_Integrity_Risk_Report_AY2026-27.csv"
    },
    {
        "id": "trust-distribution-report",
        "name": "Trust Distribution Report",
        "desc": "L0–L4 breakdown with verification evidence coverage",
        "updated": "20 Oct 2026",
        "format": "CSV",
        "filename": "AICTE_Trust_Distribution_Report.csv"
    },
    {
        "id": "seat-ledger-audit-export",
        "name": "Seat Ledger Audit Export",
        "desc": "All seat claims with slot numbers, pool status and nightly invariant results",
        "updated": "21 Oct 2026",
        "format": "CSV",
        "filename": "AICTE_Seat_Ledger_Audit_Ledger.csv"
    },
    {
        "id": "case-resolution-performance",
        "name": "Case Resolution Performance",
        "desc": "SLA compliance, case age, officer assignments, resolution outcomes",
        "updated": "19 Oct 2026",
        "format": "CSV",
        "filename": "AICTE_Case_Resolution_SLA_Report.csv"
    },
    {
        "id": "cross-institution-duplicate-log",
        "name": "Cross-Institution Duplicate Log",
        "desc": "All CONFLICT_HOLD events, mediation outcomes and identity merge journal",
        "updated": "18 Oct 2026",
        "format": "CSV",
        "filename": "AICTE_Cross_Institution_Duplicate_Log.csv"
    },
    {
        "id": "policy-backtest-report",
        "name": "Policy Back-test Report",
        "desc": "Impact analysis of policy version 7 vs version 6 — newly flagged institutions",
        "updated": "15 Oct 2026",
        "format": "CSV",
        "filename": "AICTE_Policy_Studio_Backtest_v7.csv"
    },
    {
        "id": "full-data-export-anonymised",
        "name": "Full Data Export (Anonymised)",
        "desc": "Complete dataset with PII removed — for authorised policy research",
        "updated": "01 Oct 2026",
        "format": "JSON",
        "filename": "AICTE_Full_Anonymised_Dataset_2026.json"
    }
]

@router.get("/list")
def get_reports_list():
    return REPORT_METADATA

@router.get("/download/{report_id}")
def download_report(report_id: str):
    meta = next((r for r in REPORT_METADATA if r["id"] == report_id), None)
    if not meta:
        raise HTTPException(status_code=404, detail="Report not found")

    output = io.StringIO()

    if report_id == "national-enrolment-summary":
        writer = csv.writer(output)
        writer.writerow(["Institution ID", "Institution Name", "State", "Type", "Approved Intake", "Enrolled Count", "Verified Count", "Integrity Band", "Integrity Score"])
        for i in state.institutions:
            writer.writerow([i["id"], i["name"], i["state"], i["type"], i["approvedIntake"], i["enrolledCount"], i["verifiedCount"], i["integrityBand"], i["integrityScore"]])
        content = output.getvalue()
        media_type = "text/csv"

    elif report_id == "integrity-risk-report":
        writer = csv.writer(output)
        writer.writerow(["Case ID", "Case Type", "Severity", "Institution", "Status", "Assigned Officer", "SLA Due Date", "Opened At", "Description"])
        for c in state.cases:
            writer.writerow([c["id"], c["caseType"], c["severity"], c["institutionName"], c["status"], c.get("assignedTo", "Unassigned"), c["slaDueAt"], c["openedAt"], c["description"]])
        content = output.getvalue()
        media_type = "text/csv"

    elif report_id == "trust-distribution-report":
        writer = csv.writer(output)
        writer.writerow(["Trust Tier", "Tier Description", "Verified Cohort Count", "Percentage Share", "Regulatory Status"])
        writer.writerow(["Level 0", "Claimed (Self-declared only)", 1200, "6.5%", "Awaiting Upload"])
        writer.writerow(["Level 1", "Format-Valid (Regex / Checksum pass)", 1600, "8.7%", "Provisional PPID"])
        writer.writerow(["Level 2", "Identity-Verified (APAAR/Aadhaar matched)", 5800, "31.5%", "Legitimate Admission"])
        writer.writerow(["Level 3", "Cross-Checked (Matriculation Board linked)", 6900, "37.5%", "Full Academic Trust"])
        writer.writerow(["Level 4", "AICTE-Certified (Direct Council Affirmation)", 2900, "15.8%", "National Council Verified"])
        content = output.getvalue()
        media_type = "text/csv"

    elif report_id == "seat-ledger-audit-export":
        writer = csv.writer(output)
        writer.writerow(["Programme / Quota", "Approved Cap", "Claimed Slots", "Excess Breach", "Pool Code", "Compliance Status"])
        pools = [
            ("B.Tech CSE", 1040, 1078, 38, "REGULAR", "BREACH"),
            ("B.Tech ECE", 540, 534, 0, "REGULAR", "OK"),
            ("B.Tech IT", 300, 312, 12, "REGULAR", "BREACH"),
            ("National NRI Quota", 420, 448, 28, "NRI", "BREACH"),
            ("Tuition Fee Waiver (TFW)", 150, 142, 0, "TFW", "OK"),
            ("Foreign Nationals (FN)", 140, 138, 0, "FN", "OK"),
            ("Supernumerary PMSSS", 100, 96, 0, "PMSSS", "OK")
        ]
        for p in pools:
            writer.writerow(list(p))
        content = output.getvalue()
        media_type = "text/csv"

    elif report_id == "case-resolution-performance":
        writer = csv.writer(output)
        writer.writerow(["Case ID", "Severity", "Assigned Officer", "Resolution Status", "SLA Status", "Closed Timestamp", "Recorded Outcome"])
        for c in state.cases:
            sla_status = "COMPLIANT" if c["status"] in ["Resolved", "Closed"] else "ACTIVE"
            writer.writerow([c["id"], c["severity"], c.get("assignedTo", "Unassigned"), c["status"], sla_status, c.get("closedAt", "—"), c.get("outcome", "Pending Investigation")])
        content = output.getvalue()
        media_type = "text/csv"

    elif report_id == "cross-institution-duplicate-log":
        writer = csv.writer(output)
        writer.writerow(["Journal ID", "Survivor Identity", "Absorbed Duplicate", "Match Method", "Confidence Score", "Approving Authority", "Consolidated At", "Mediation Rationale"])
        for m in state.merge_journal:
            writer.writerow([m["id"], m["survivor"], m["absorbed"], m["method"], f"{int(m['confidence']*100)}%", m["approvedBy"], m["mergedAt"], m["reason"]])
        content = output.getvalue()
        media_type = "text/csv"

    elif report_id == "policy-backtest-report":
        writer = csv.writer(output)
        writer.writerow(["Rule ID", "Rule Name", "Category", "Enforcement Stage", "Flagged Records", "Affected Institutions", "Last Backtest"])
        for r in state.policy_engine.get_rules():
            writer.writerow([r["id"], r["name"], r["category"], r["currentStage"], r["flaggedCount"], r["affectedInstitutions"], r["lastBacktest"]])
        content = output.getvalue()
        media_type = "text/csv"

    elif report_id == "full-data-export-anonymised":
        data = {
            "metadata": {
                "organization": "All India Council for Technical Education (AICTE)",
                "system": "APAAR-Pramaan Officer Governance Platform",
                "exportTimestamp": "2026-10-22T21:30:00Z",
                "piiSanitized": True
            },
            "institutionsSummary": state.institutions,
            "anonymizedEnrolmentsSample": state.students,
            "policyRules": state.policy_engine.get_rules(),
            "auditChainVerification": state.audit_engine.verify_integrity()
        }
        content = json.dumps(data, indent=2)
        media_type = "application/json"
    else:
        content = "AICTE Report Export"
        media_type = "text/plain"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{meta["filename"]}"'
        }
    )
