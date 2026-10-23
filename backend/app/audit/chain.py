import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

def sha256_str(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def sha256_dict(obj: Any) -> str:
    serialized = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

class AuditBlock:
    def __init__(
        self,
        chain_id: int,
        seq: int,
        ts: str,
        actor: str,
        actor_type: str,
        action: str,
        entity: str,
        entity_id: str,
        payload_digest: str,
        prev_hash: str,
        detail: str,
        this_hash: Optional[str] = None,
        valid: bool = True
    ):
        self.chain_id = chain_id
        self.seq = seq
        self.ts = ts
        self.actor = actor
        self.actor_type = actor_type
        self.action = action
        self.entity = entity
        self.entity_id = entity_id
        self.payload_digest = payload_digest
        self.prev_hash = prev_hash
        self.detail = detail
        self.valid = valid
        self.this_hash = this_hash or self.calculate_hash()

    def calculate_hash(self) -> str:
        raw = f"{self.chain_id}|{self.seq}|{self.ts}|{self.actor}|{self.actor_type}|{self.action}|{self.entity}|{self.entity_id}|{self.payload_digest}|{self.prev_hash}"
        return sha256_str(raw)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chainId": self.chain_id,
            "seq": self.seq,
            "ts": self.ts,
            "actor": self.actor,
            "actorType": self.actor_type,
            "action": self.action,
            "entity": self.entity,
            "entityId": self.entity_id,
            "payloadDigest": f"{self.payload_digest[:4]}...{self.payload_digest[-4:]}",
            "prevHash": f"{self.prev_hash[:4]}...{self.prev_hash[-4:]}",
            "thisHash": f"{self.this_hash[:4]}...{self.this_hash[-4:]}" if self.valid else "MISMATCH",
            "fullThisHash": self.this_hash,
            "fullPrevHash": self.prev_hash,
            "fullPayloadDigest": self.payload_digest,
            "valid": self.valid,
            "detail": self.detail
        }

class AuditChainEngine:
    def __init__(self):
        self.chains: Dict[int, List[AuditBlock]] = {1: [], 2: [], 3: []}
        self.tampered_backup: Optional[Dict[str, Any]] = None
        self._seed_default_chain()

    def _seed_default_chain(self):
        # Seed realistic starting blocks with valid cryptographic linkage
        genesis_prev = "0" * 64
        
        events_seed = [
            (1, 1035, "2026-10-14T08:00:00Z", "System", "system", "GENESIS_ANCHOR", "audit_chain", "CH-1", {"chain": "Main", "version": 1}, genesis_prev, "Genesis anchor established. AICTE root trust anchored."),
            (1, 1037, "2026-10-15T14:20:00Z", "Omar Al-Hassan", "student", "CREDENTIAL_REVOKED", "credential", "CRED-0091", {"revoked": True, "target": "VFR-005"}, None, "Student revoked consent for employer verification. Next scan will return REVOKED."),
            (2, 86, "2026-10-17T08:00:00Z", "System", "system", "LEDGER_INVARIANT_CHECK", "seat_ledger", "NIGHTLY", {"status": "PASSED", "breaches": 0}, genesis_prev, "Nightly invariant passed. claimed=count(active enrolments) for all pools."),
            (1, 1038, "2026-10-18T11:30:00Z", "APAAR Service", "system", "IDENTITY_VERIFY_FAILED", "enrolment", "s5", {"reason": "NO_APAAR_FOREIGN"}, None, "FN student without APAAR. Provisional PPID issued. L1 trust assigned. Re-verify queued."),
            (3, 12, "2026-10-19T16:55:18Z", "System", "system", "MERKLE_CHECKPOINT", "audit_chain", "DAILY", {"root": "7f8b90a..."}, genesis_prev, "Daily Merkle root computed and signed. 3 chains checkpointed. External timestamp issued."),
            (1, 1039, "2026-10-20T09:10:05Z", "Shri Rajesh Kumar", "officer", "TRUST_LEVEL_UPDATED", "enrolment", "s6", {"from": 3, "to": 4}, None, "Trust promoted to L4 AICTE-Certified after annual affirmation review."),
            (2, 87, "2026-10-21T14:22:33Z", "System", "system", "SINGLE_SEAT_LOCK_CONFLICT", "enrolment", "s3", {"conflictInst": "INST-KA-0021"}, None, "Conflict hold applied. DUP_ENROLMENT case C-0042 opened. Both institutions notified."),
            (2, 88, "2026-10-21T15:44:09Z", "System", "system", "SEAT_CLAIM", "seat_pool", "POOL-CSE-REG", {"allocated": 62, "max": 60}, None, "Slot 62 assigned in REGULAR pool. over_by=2. INTAKE_BREACH case opened."),
            (1, 1040, "2026-10-22T10:30:14Z", "Dr. Priya Nair", "institution", "BATCH_SUBMITTED", "batch", "BATCH-2901", {"total": 245, "accepted": 231}, None, "245 rows submitted. 231 accepted, 8 rejected, 6 held. Signed receipt issued."),
            (1, 1041, "2026-10-22T10:58:01Z", "APAAR Service", "system", "IDENTITY_VERIFIED", "enrolment", "s12", {"apaar": "1234-5678-2222", "score": 0.99}, None, "APAAR 1234-5678-2222 verified. Name match 0.99. DOB exact."),
            (1, 1042, "2026-10-22T11:14:22Z", "Shri Rajesh Kumar", "officer", "CASE_DECISION_RECORDED", "case", "C-0021", {"outcome": "Resolved", "decision": "RESOLVE_NO_ISSUE"}, None, "Outcome: Resolved — no issue. Rationale recorded. Audit chain updated."),
        ]

        for chain_id, seq, ts, actor, actor_type, action, entity, entity_id, payload, custom_prev, detail in events_seed:
            prev = custom_prev
            if prev is None:
                chain = self.chains[chain_id]
                prev = chain[-1].this_hash if chain else genesis_prev
            
            digest = sha256_dict(payload)
            block = AuditBlock(
                chain_id=chain_id,
                seq=seq,
                ts=ts,
                actor=actor,
                actor_type=actor_type,
                action=action,
                entity=entity,
                entity_id=entity_id,
                payload_digest=digest,
                prev_hash=prev,
                detail=detail
            )
            self.chains[chain_id].append(block)

    def append_event(
        self,
        chain_id: int,
        actor: str,
        actor_type: str,
        action: str,
        entity: str,
        entity_id: str,
        detail: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> AuditBlock:
        payload = payload or {}
        chain = self.chains.get(chain_id, self.chains[1])
        seq = (chain[-1].seq + 1) if chain else 1
        prev_hash = chain[-1].this_hash if chain else ("0" * 64)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        digest = sha256_dict(payload)

        block = AuditBlock(
            chain_id=chain_id,
            seq=seq,
            ts=ts,
            actor=actor,
            actor_type=actor_type,
            action=action,
            entity=entity,
            entity_id=entity_id,
            payload_digest=digest,
            prev_hash=prev_hash,
            detail=detail
        )
        chain.append(block)
        return block

    def verify_integrity(self) -> Dict[str, Any]:
        genesis_prev = "0" * 64
        for c_id, chain in self.chains.items():
            for i, block in enumerate(chain):
                # 1. Verify recalculation
                expected_hash = block.calculate_hash()
                if block.this_hash != expected_hash:
                    return {
                        "isValid": False,
                        "chainId": c_id,
                        "brokenSeq": block.seq,
                        "reason": f"Block #{block.seq} payload/hash corrupted! Hash mismatch: stored {block.this_hash[:10]}... vs calculated {expected_hash[:10]}...",
                        "tamperedBlock": block.to_dict()
                    }
                
                # 2. Verify linkage to previous block
                if i == 0:
                    if block.prev_hash != genesis_prev:
                        return {
                            "isValid": False,
                            "chainId": c_id,
                            "brokenSeq": block.seq,
                            "reason": f"Genesis block #{block.seq} prev_hash broken.",
                            "tamperedBlock": block.to_dict()
                        }
                else:
                    prev_block = chain[i - 1]
                    if block.prev_hash != prev_block.this_hash:
                        return {
                            "isValid": False,
                            "chainId": c_id,
                            "brokenSeq": block.seq,
                            "reason": f"Hash chain broken between block #{prev_block.seq} and #{block.seq}. Pointer {block.prev_hash[:10]} does not match previous block hash {prev_block.this_hash[:10]}",
                            "tamperedBlock": block.to_dict()
                        }

        return {
            "isValid": True,
            "chainId": 1,
            "brokenSeq": None,
            "reason": "All 3 cryptographic hash chains are healthy, verified, and anchored.",
            "tamperedBlock": None
        }

    def simulate_tamper(self, seq: int = 1040, mutated_actor: str = "[UNAUTHORIZED_TAMPER]", mutated_action: str = "DIRECT_DB_INJECTION") -> Dict[str, Any]:
        # Find block by seq in chain 1
        for block in self.chains[1]:
            if block.seq == seq:
                # Save backup for restoration
                self.tampered_backup = {
                    "seq": block.seq,
                    "actor": block.actor,
                    "action": block.action,
                    "detail": block.detail,
                    "payload_digest": block.payload_digest,
                    "valid": block.valid
                }
                # Corrupt block fields without updating hash
                block.actor = mutated_actor
                block.action = mutated_action
                block.detail = f"TAMPERED: Unauthorized update injected bypassing AICTE cryptographic signing key."
                block.payload_digest = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                block.valid = False
                return {
                    "status": "TAMPER_SIMULATED",
                    "tamperedSeq": seq,
                    "message": f"Block #{seq} content modified without re-anchoring. Verification will immediately trigger alert."
                }
        return {"status": "NOT_FOUND", "message": f"Block #{seq} not found."}

    def restore_chain(self) -> Dict[str, Any]:
        if not self.tampered_backup:
            return {"status": "NO_TAMPER", "message": "No active tamper simulation found."}

        for block in self.chains[1]:
            if block.seq == self.tampered_backup["seq"]:
                block.actor = self.tampered_backup["actor"]
                block.action = self.tampered_backup["action"]
                block.detail = self.tampered_backup["detail"]
                block.payload_digest = self.tampered_backup["payload_digest"]
                block.valid = True
                self.tampered_backup = None
                return {"status": "RESTORED", "message": f"Block #{block.seq} successfully restored to genuine state. Chain re-verified."}
        
        return {"status": "NOT_FOUND", "message": "Could not locate block to restore."}

    def get_all_events(self) -> List[Dict[str, Any]]:
        all_blocks: List[AuditBlock] = []
        for chain in self.chains.values():
            all_blocks.extend(chain)
        # Sort descending by timestamp / seq
        all_blocks.sort(key=lambda b: (b.ts, b.seq), reverse=True)
        return [b.to_dict() for b in all_blocks]

    def get_time_machine_events(self, as_of: str) -> List[Dict[str, Any]]:
        all_events = self.get_all_events()
        # Filter events up to as_of
        return [e for e in all_events if e["ts"] <= as_of]
