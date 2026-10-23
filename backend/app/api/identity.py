from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from app.db.state import state
from app.models import MergeRequest

router = APIRouter(prefix="/api/identity", tags=["Identity Graph"])

@router.get("/records")
def get_identity_records(search: Optional[str] = None):
    res = state.identity_records
    if search:
        s = search.lower()
        res = [
            r for r in res
            if s in r["name"].lower()
            or s in r["personId"].lower()
            or s in (r.get("apaarId") or "").lower()
            or s in (r.get("ppid") or "").lower()
            or s in r["institution"].lower()
        ]
    return res

@router.get("/journal")
def get_merge_journal():
    return state.merge_journal

@router.post("/merge")
def execute_identity_merge(req: MergeRequest):
    survivor = next((r for r in state.identity_records if r["personId"] == req.survivorId), None)
    absorbed = next((r for r in state.identity_records if r["personId"] == req.absorbedId), None)

    if not survivor or not absorbed:
        raise HTTPException(status_code=404, detail="Survivor or Absorbed record not found in identity graph.")

    # Mark absorbed as merged
    absorbed["mergedInto"] = req.survivorId
    absorbed["status"] = "VERIFIED"
    survivor["trustLevel"] = max(survivor["trustLevel"], absorbed["trustLevel"])

    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    journal_entry = {
        "id": f"MJ-00{len(state.merge_journal) + 1}",
        "survivor": req.survivorId,
        "absorbed": req.absorbedId,
        "method": "OFFICER_APPROVED",
        "confidence": 0.98,
        "approvedBy": req.officerName,
        "mergedAt": now_ts,
        "undoneAt": None,
        "reason": req.rationale
    }
    state.merge_journal.insert(0, journal_entry)

    # Append to cryptographic audit chain
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=req.officerName,
        actor_type="officer",
        action="IDENTITY_MERGED",
        entity="person",
        entity_id=req.survivorId,
        detail=f"Officer {req.officerName} merged identity {req.absorbedId} into {req.survivorId}. Rationale: {req.rationale}",
        payload={"survivor": req.survivorId, "absorbed": req.absorbedId, "journalId": journal_entry["id"]}
    )

    return {
        "status": "SUCCESS",
        "journalEntry": journal_entry,
        "auditBlockSeq": block.seq,
        "message": f"Identity {req.absorbedId} successfully consolidated into {req.survivorId}."
    }

@router.post("/undo-merge/{journal_id}")
def undo_merge(journal_id: str, officer_name: str = "Shri Rajesh Kumar"):
    entry = next((j for j in state.merge_journal if j["id"] == journal_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Merge journal entry not found")
    if entry.get("undoneAt"):
        raise HTTPException(status_code=400, detail="Merge has already been undone.")

    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry["undoneAt"] = now_ts

    # Revert absorbed record
    absorbed = next((r for r in state.identity_records if r["personId"] == entry["absorbed"]), None)
    if absorbed:
        absorbed["mergedInto"] = None
        absorbed["status"] = "CANDIDATE"

    # Append to cryptographic audit chain
    block = state.audit_engine.append_event(
        chain_id=1,
        actor=officer_name,
        actor_type="officer",
        action="IDENTITY_MERGE_UNDONE",
        entity="person",
        entity_id=entry["survivor"],
        detail=f"Officer {officer_name} undid consolidation {journal_id}: separated {entry['absorbed']} from {entry['survivor']}.",
        payload={"journalId": journal_id, "survivor": entry["survivor"], "absorbed": entry["absorbed"]}
    )

    return {
        "status": "SUCCESS",
        "journalEntry": entry,
        "auditBlockSeq": block.seq,
        "message": f"Consolidation {journal_id} successfully reversed."
    }

@router.post("/fuzzy-check")
def fuzzy_match_check(record1: Dict[str, Any], record2: Dict[str, Any]):
    return state.identity_resolver.compute_similarity(record1, record2)
