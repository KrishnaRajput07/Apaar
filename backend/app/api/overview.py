from fastapi import APIRouter
from app.db.state import state

router = APIRouter(prefix="/api/overview", tags=["Overview"])

@router.get("/metrics")
def get_metrics():
    total_enrolments = len(state.students) * 1530 # Scaling factor to reflect national 18.4K cohort
    verified_count = sum(1 for s in state.students if s["trustLevel"] >= 2) * 1530
    open_cases = sum(1 for c in state.cases if c["status"] not in ["Resolved", "Closed"])
    critical_cases = sum(1 for c in state.cases if c["severity"] in ["CRITICAL", "HIGH"] and c["status"] not in ["Resolved", "Closed"])
    breach_insts = sum(1 for i in state.institutions if i["enrolledCount"] > i["approvedIntake"])

    return [
        {
            "label": "Total Enrolment Records",
            "value": total_enrolments,
            "sublabel": f"{verified_count:,} identity-verified (L2+)",
            "color": "brand",
            "delta": "+1,240 this week",
            "deltaType": "up"
        },
        {
            "label": "Institutions Onboarded",
            "value": len(state.institutions),
            "sublabel": f"{len(state.institutions)} active submissions verified",
            "color": "info",
            "delta": "100% onboarded",
            "deltaType": "neutral"
        },
        {
            "label": "Open Cases",
            "value": open_cases,
            "sublabel": f"{critical_cases} critical / high priority",
            "color": "danger",
            "delta": "−3 since last week",
            "deltaType": "down"
        },
        {
            "label": "Seat Breaches Detected",
            "value": breach_insts,
            "sublabel": "2 REGULAR · 1 NRI/FN pool",
            "color": "warning",
            "delta": "1 new today",
            "deltaType": "neutral"
        }
    ]

@router.get("/enrolment-trend")
def get_enrolment_trend():
    return [
        {"name": "May '26", "enrolled": 1200, "verified": 950,  "cases": 2},
        {"name": "Jun '26", "enrolled": 3400, "verified": 2800, "cases": 5},
        {"name": "Jul '26", "enrolled": 7800, "verified": 6900, "cases": 12},
        {"name": "Aug '26", "enrolled": 13200, "verified": 11400, "cases": 18},
        {"name": "Sep '26", "enrolled": 16900, "verified": 14200, "cases": 24},
        {"name": "Oct '26", "enrolled": 18400, "verified": 15600, "cases": 7},
    ]

@router.get("/trust-distribution")
def get_trust_distribution():
    return [
        {"name": "L0 Claimed",          "value": 1200, "color": "#8791A5"},
        {"name": "L1 Format-Valid",     "value": 1600, "color": "#B7791F"},
        {"name": "L2 Identity-Verified","value": 5800, "color": "#2F6FED"},
        {"name": "L3 Cross-Checked",    "value": 6900, "color": "#6558D3"},
        {"name": "L4 AICTE-Certified",  "value": 2900, "color": "#198754"},
    ]

@router.get("/cases-by-type")
def get_cases_by_type():
    counts: dict = {}
    for c in state.cases:
        ctype = c["caseType"]
        counts[ctype] = counts.get(ctype, 0) + 1
    
    color_map = {
        "DUP_ENROLMENT": "#C53B45",
        "INTAKE_BREACH": "#E05666",
        "DECLARATION_MISMATCH": "#B7791F",
        "DATA_MISMATCH": "#D99B26",
        "POSSIBLE_SAME_PERSON": "#6558D3",
        "INVALID_ID": "#2F6FED",
        "ANOMALY": "#8791A5"
    }

    return [
        {"name": k.replace("_", " ").title(), "value": v, "color": color_map.get(k, "#6558D3")}
        for k, v in counts.items()
    ]

@router.get("/regional-distribution")
def get_regional_distribution():
    return [
        {"name": "South", "value": 6800, "color": "#2F6FED"},
        {"name": "West",  "value": 4900, "color": "#2F6FED"},
        {"name": "North", "value": 4200, "color": "#2F6FED"},
        {"name": "East",  "value": 2500, "color": "#2F6FED"},
    ]

@router.get("/critical-cases")
def get_critical_cases():
    return [c for c in state.cases if c["severity"] in ["CRITICAL", "HIGH"] and c["status"] not in ["Resolved", "Closed"]][:3]

@router.get("/risk-institutions")
def get_risk_institutions():
    return sorted(state.institutions, key=lambda x: x["openCases"], reverse=True)[:4]

@router.get("/timeline")
def get_timeline():
    events = state.audit_engine.get_all_events()[:6]
    return [
        {
            "id": f"evt-{e['seq']}",
            "actor": e["actor"],
            "action": e["action"].replace("_", " ").title(),
            "detail": e["detail"],
            "at": e["ts"],
            "type": "danger" if not e["valid"] or "BREACH" in e["action"] or "CONFLICT" in e["action"] else "success" if "VERIFIED" in e["action"] or "DECISION" in e["action"] else "info"
        }
        for e in events
    ]
