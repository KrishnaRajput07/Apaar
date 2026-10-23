from fastapi import APIRouter
from typing import Optional
from app.db.state import state
from app.models import TamperSimulationRequest

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])

@router.get("/chain")
def get_audit_chain(search: Optional[str] = None):
    events = state.audit_engine.get_all_events()
    if search:
        s = search.lower()
        events = [
            e for e in events
            if s in e["actor"].lower()
            or s in e["action"].lower()
            or s in e["entity"].lower()
            or s in e["entityId"].lower()
            or s in e["detail"].lower()
        ]
    return events

@router.get("/verify")
def verify_audit_chain():
    """
    Executes SHA-256 cryptographic proof verification across all blocks in the ledger.
    """
    return state.audit_engine.verify_integrity()

@router.post("/tamper")
def simulate_tamper(req: TamperSimulationRequest):
    """
    Simulates an unauthorized record modification without cryptographic signing,
    demonstrating the system's instant tamper-detection capability.
    """
    return state.audit_engine.simulate_tamper(
        seq=req.seq,
        mutated_actor=req.tamperedActor,
        mutated_action=req.tamperedAction
    )

@router.post("/restore")
def restore_chain():
    """
    Restores tampered blocks back to verified state and re-anchors the chain.
    """
    res = state.audit_engine.restore_chain()
    verification = state.audit_engine.verify_integrity()
    return {**res, "chainVerification": verification}

@router.get("/time-machine")
def time_machine_replay(as_of: str):
    """
    Replays system state and event log as of historical timestamp.
    """
    events = state.audit_engine.get_time_machine_events(as_of)
    return {
        "asOf": as_of,
        "eventsCountAtSnapshot": len(events),
        "events": events
    }
