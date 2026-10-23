"""Audit router — hash-chained event log, tamper detection, time machine."""
import json
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..core.database import get_db
from ..core.security import get_current_user, compute_event_hash
from ..models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events")
def list_events(
    chain_id: int = 1,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    events = db.query(AuditEvent).filter(AuditEvent.chain_id == chain_id).order_by(AuditEvent.seq.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": e.id,
            "chain_id": e.chain_id,
            "seq": e.seq,
            "actor": e.actor,
            "actor_type": e.actor_type,
            "action": e.action,
            "entity": e.entity,
            "entity_id": e.entity_id,
            "payload": e.payload,
            "payload_digest": e.payload_digest,
            "this_hash": e.this_hash,
            "valid": _verify_chain_link(db, e),
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/chains")
def get_chains(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get health status of all audit chains."""
    chains = db.query(AuditEvent.chain_id).distinct().all()
    result = []
    for (cid,) in chains:
        count = db.query(AuditEvent).filter(AuditEvent.chain_id == cid).count()
        last = db.query(AuditEvent).filter(AuditEvent.chain_id == cid).order_by(AuditEvent.seq.desc()).first()
        # Verify chain integrity
        events = db.query(AuditEvent).filter(AuditEvent.chain_id == cid).order_by(AuditEvent.seq).all()
        valid = _verify_full_chain(events)
        result.append({
            "chain_id": cid,
            "event_count": count,
            "valid": valid,
            "last_event_seq": last.seq if last else 0,
            "last_event_at": last.created_at.isoformat() if last else None,
        })
    return result


@router.post("/events")
def append_event(
    action: str,
    entity: str,
    entity_id: str,
    actor: str = "System",
    actor_type: str = "system",
    payload: dict = {},
    chain_id: int = 1,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Append a new audit event to the chain."""
    # Get previous hash
    last = db.query(AuditEvent).filter(AuditEvent.chain_id == chain_id).order_by(AuditEvent.seq.desc()).first()
    prev_hash = last.this_hash if last else "0" * 64
    seq = (last.seq + 1) if last else 1

    # Compute hash
    raw = prev_hash + json.dumps(payload, sort_keys=True, default=str)
    this_hash = hashlib.sha256(raw.encode()).hexdigest()
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

    event = AuditEvent(
        id=f"AUD-{seq:04d}",
        chain_id=chain_id,
        seq=seq,
        actor=actor,
        actor_type=actor_type,
        action=action,
        entity=entity,
        entity_id=entity_id,
        payload=payload,
        payload_digest=digest,
        prev_hash=prev_hash,
        this_hash=this_hash,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "seq": seq,
        "chain_id": chain_id,
        "this_hash": this_hash,
        "created_at": event.created_at.isoformat(),
    }


@router.get("/time-machine")
def time_machine(
    as_of: str,  # ISO date string
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Query what the system knew as of a given date (bitemporal)."""
    as_of_date = datetime.fromisoformat(as_of).replace(tzinfo=timezone.utc)

    # Count events up to that date
    events_before = db.query(AuditEvent).filter(AuditEvent.created_at <= as_of_date).all()

    # Aggregate counts
    enrolments = sum(1 for e in events_before if e.action == "ENROLMENT_CREATED")
    verified = sum(1 for e in events_before if e.action == "IDENTITY_VERIFIED")
    cases = sum(1 for e in events_before if e.action in ["CASE_OPENED", "INTAKE_BREACH"])

    return {
        "as_of": as_of,
        "records_known": enrolments,
        "identity_verified": verified,
        "cases_open": cases,
        "events_count": len(events_before),
    }


def _verify_chain_link(db: Session, event: AuditEvent) -> bool:
    """Verify a single chain link by recomputing the hash."""
    raw = event.prev_hash + json.dumps(event.payload, sort_keys=True, default=str)
    computed = hashlib.sha256(raw.encode()).hexdigest()
    return computed == event.this_hash


def _verify_full_chain(events: list[AuditEvent]) -> bool:
    """Verify the entire chain from genesis."""
    prev_hash = "0" * 64
    for e in events:
        if e.prev_hash != prev_hash:
            return False
        raw = prev_hash + json.dumps(e.payload, sort_keys=True, default=str)
        computed = hashlib.sha256(raw.encode()).hexdigest()
        if computed != e.this_hash:
            return False
        prev_hash = e.this_hash
    return True
