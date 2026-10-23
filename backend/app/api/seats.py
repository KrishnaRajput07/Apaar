from fastapi import APIRouter
from app.db.state import state

router = APIRouter(prefix="/api/seats", tags=["Seat Ledger"])

@router.get("/summary")
def get_seat_summary():
    total_approved = sum(i["approvedIntake"] for i in state.institutions)
    total_enrolled = sum(i["enrolledCount"] for i in state.institutions)
    breach_insts = [i for i in state.institutions if i["enrolledCount"] > i["approvedIntake"]]
    util_pct = round((total_enrolled / total_approved) * 100, 1) if total_approved > 0 else 0

    return {
        "totalApprovedIntake": total_approved,
        "totalEnrolled": total_enrolled,
        "seatBreachesCount": len(breach_insts),
        "breachInstitutions": [i["name"] for i in breach_insts],
        "seatsRemaining": max(0, total_approved - total_enrolled),
        "overallUtilizationPercent": util_pct,
        "academicYear": "2026-27"
    }

@router.get("/institutions")
def get_institution_seats():
    return [
        {
            "id": inst["id"],
            "name": inst["name"],
            "state": inst["state"],
            "type": inst["type"],
            "approvedIntake": inst["approvedIntake"],
            "enrolledCount": inst["enrolledCount"],
            "utilizationPercent": round((inst["enrolledCount"] / inst["approvedIntake"]) * 100),
            "status": "BREACH" if inst["enrolledCount"] > inst["approvedIntake"] else "WARNING" if inst["enrolledCount"] / inst["approvedIntake"] > 0.95 else "OK",
            "overBy": max(0, inst["enrolledCount"] - inst["approvedIntake"]),
            "programmes": inst.get("programmes", [])
        }
        for inst in state.institutions
    ]

@router.get("/pools")
def get_seat_pools():
    return [
        {"programme": "B.Tech CSE", "approved": 1040, "claimed": 1078, "overBy": 38, "poolCode": "REGULAR", "status": "BREACH"},
        {"programme": "B.Tech ECE", "approved": 540,  "claimed": 534,  "overBy": 0,  "poolCode": "REGULAR", "status": "OK"},
        {"programme": "B.Tech IT",  "approved": 300,  "claimed": 312,  "overBy": 12, "poolCode": "REGULAR", "status": "BREACH"},
        {"programme": "National NRI Quota", "approved": 420, "claimed": 448, "overBy": 28, "poolCode": "NRI", "status": "BREACH"},
        {"programme": "Tuition Fee Waiver (TFW)", "approved": 150, "claimed": 142, "overBy": 0, "poolCode": "TFW", "status": "OK"},
        {"programme": "Foreign Nationals (FN)", "approved": 140, "claimed": 138, "overBy": 0, "poolCode": "FN", "status": "OK"},
        {"programme": "Supernumerary PMSSS", "approved": 100, "claimed": 96, "overBy": 0, "poolCode": "PMSSS", "status": "OK"},
    ]
