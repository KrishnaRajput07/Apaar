"""
Mock APAAR adapter — simulates the real APAAR identity verification API.
In production, swap this with the real APAAR/DigiLocker adapter.
All responses are labelled as SIMULATION.
"""
import random
import hashlib
from dataclasses import dataclass


@dataclass
class ApaarVerifyResult:
    apaar_id: str
    verified: bool
    name_match: float       # 0-1 Jaro-Winkler similarity
    dob_match: bool
    photo_match: bool
    error: str | None = None


# In-memory registry of known APAAR IDs (seeded by the data seeder)
_KNOWN_APAAR: dict[str, dict] = {}


def seed_known_apaar(apaar_id: str, name: str, dob: str, photo_hash: str):
    """Called by the seeder to register a known identity."""
    _KNOWN_APAAR[apaar_id] = {"name": name, "dob": dob, "photo_hash": photo_hash}


def verify_apaar(apaar_id: str, submitted_name: str = "", submitted_dob: str = "") -> ApaarVerifyResult:
    """
    Simulates an APAAR verification call.
    Returns match scores against the registered identity.
    """
    record = _KNOWN_APAAR.get(apaar_id)

    if not record:
        return ApaarVerifyResult(
            apaar_id=apaar_id,
            verified=False,
            name_match=0.0,
            dob_match=False,
            photo_match=False,
            error="APAAR_ID_NOT_FOUND",
        )

    # Simulate name similarity (Jaro-Winkler-like)
    from rapidfuzz import fuzz
    name_sim = fuzz.ratio(submitted_name.lower(), record["name"].lower()) / 100.0

    dob_match = submitted_dob == record["dob"] if submitted_dob else True

    # Simulate photo match (random high value for known IDs)
    photo_match = random.random() > 0.05  # 95% pass rate

    verified = name_sim > 0.85 and dob_match and photo_match

    return ApaarVerifyResult(
        apaar_id=apaar_id,
        verified=verified,
        name_match=round(name_sim, 4),
        dob_match=dob_match,
        photo_match=photo_match,
        error=None if verified else "VERIFICATION_FAILED",
    )


def generate_apaar_id() -> str:
    """Generate a realistic 12-digit APAAR ID."""
    return f"{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"


def generate_ppid() -> str:
    """Generate a Provisional Person ID for FN/OCI/NRI without APAAR."""
    return f"PPID-{random.randint(10000,99999)}"
