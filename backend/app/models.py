"""
All SQLAlchemy ORM models for APAAR Pramaan.
Single file keeps imports simple and avoids circular dependencies.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, Enum as SAEnum, JSON, BigInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from .core.database import Base

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


# ── User / Auth ───────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id:              Mapped[str]            = mapped_column(String(36), primary_key=True, default=new_uuid)
    email:           Mapped[str]            = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str]            = mapped_column(String(255), nullable=False)
    full_name:       Mapped[str]            = mapped_column(String(255), nullable=False)
    role:            Mapped[str]            = mapped_column(String(50), nullable=False)   # student|institution|officer
    institution_id:  Mapped[Optional[str]]  = mapped_column(String(36), ForeignKey("institutions.id"), nullable=True)
    student_id:      Mapped[Optional[str]]  = mapped_column(String(36), ForeignKey("students.id"), nullable=True)
    is_active:       Mapped[bool]           = mapped_column(Boolean, default=True)
    created_at:      Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=now_utc)

    institution: Mapped[Optional["Institution"]] = relationship("Institution", back_populates="users")


# ── Institution ───────────────────────────────────────────────────
class Institution(Base):
    __tablename__ = "institutions"

    id:               Mapped[str]  = mapped_column(String(36), primary_key=True, default=new_uuid)
    name:             Mapped[str]  = mapped_column(String(500), nullable=False)
    aicte_code:       Mapped[str]  = mapped_column(String(50), unique=True, nullable=False, index=True)
    state:            Mapped[str]  = mapped_column(String(100), nullable=False)
    district:         Mapped[str]  = mapped_column(String(100), nullable=False)
    region:           Mapped[str]  = mapped_column(String(50), nullable=False)
    inst_type:        Mapped[str]  = mapped_column(String(50), nullable=False)   # Private|Government|NIT|IIT
    status:           Mapped[str]  = mapped_column(String(20), default="ACTIVE") # ACTIVE|INACTIVE|SUSPENDED
    integrity_band:   Mapped[str]  = mapped_column(String(1), default="B")       # A|B|C|D|E
    integrity_score:  Mapped[int]  = mapped_column(Integer, default=75)
    last_submission:  Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    users:       Mapped[list["User"]]       = relationship("User", back_populates="institution")
    seat_pools:  Mapped[list["SeatPool"]]   = relationship("SeatPool", back_populates="institution")
    students:    Mapped[list["Student"]]    = relationship("Student", back_populates="institution")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="institution")
    cases:       Mapped[list["Case"]]       = relationship("Case", back_populates="institution")


# ── Seat Pool ─────────────────────────────────────────────────────
class SeatPool(Base):
    __tablename__ = "seat_pools"

    id:             Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    programme:      Mapped[str] = mapped_column(String(255), nullable=False)
    pool_code:      Mapped[str] = mapped_column(String(50), nullable=False)   # REGULAR|NRI|OCI|FN|SUPERNUMERARY
    academic_year:  Mapped[str] = mapped_column(String(9), nullable=False)    # 2026-27
    approved_intake:Mapped[int] = mapped_column(Integer, nullable=False)
    claimed:        Mapped[int] = mapped_column(Integer, default=0)
    status:         Mapped[str] = mapped_column(String(10), default="OK")     # OK|WARNING|BREACH

    institution: Mapped["Institution"] = relationship("Institution", back_populates="seat_pools")
    claims:      Mapped[list["SeatClaim"]] = relationship("SeatClaim", back_populates="pool")

    __table_args__ = (
        UniqueConstraint("institution_id", "programme", "pool_code", "academic_year", name="uq_pool"),
    )


# ── Person (identity master) ──────────────────────────────────────
class Person(Base):
    __tablename__ = "persons"

    id:          Mapped[str]           = mapped_column(String(36), primary_key=True, default=new_uuid)
    apaar_id:    Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    ppid:        Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)  # provisional
    full_name:   Mapped[str]           = mapped_column(String(255), nullable=False)
    dob:         Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # YYYY-MM-DD
    gender:      Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    phone:       Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    trust_level: Mapped[int]           = mapped_column(Integer, default=0)          # 0-4
    is_merged:   Mapped[bool]          = mapped_column(Boolean, default=False)
    merged_into: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    students:    Mapped[list["Student"]] = relationship("Student", back_populates="person")


# ── Student ───────────────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    id:             Mapped[str]           = mapped_column(String(36), primary_key=True, default=new_uuid)
    masked_id:      Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)
    person_id:      Mapped[str]           = mapped_column(String(36), ForeignKey("persons.id"), nullable=False, index=True)
    institution_id: Mapped[str]           = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    programme:      Mapped[str]           = mapped_column(String(255), nullable=False)
    academic_year:  Mapped[str]           = mapped_column(String(9), nullable=False)
    pool_code:      Mapped[str]           = mapped_column(String(50), nullable=False)
    status:         Mapped[str]           = mapped_column(String(20), default="ADMITTED")
    hold_state:     Mapped[str]           = mapped_column(String(30), default="NONE")  # NONE|CONFLICT_HOLD|IDENTITY_HOLD
    trust_level:    Mapped[int]           = mapped_column(Integer, default=0)
    risk_score:     Mapped[int]           = mapped_column(Integer, default=0)
    admission_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    batch_id:       Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    person:      Mapped["Person"]          = relationship("Person", back_populates="students")
    institution: Mapped["Institution"]     = relationship("Institution", back_populates="students")
    seat_claim:  Mapped[Optional["SeatClaim"]] = relationship("SeatClaim", back_populates="student", uselist=False)
    credentials: Mapped[list["Credential"]]    = relationship("Credential", back_populates="student")


# ── Seat Claim ────────────────────────────────────────────────────
class SeatClaim(Base):
    __tablename__ = "seat_claims"

    id:         Mapped[str]           = mapped_column(String(36), primary_key=True, default=new_uuid)
    pool_id:    Mapped[str]           = mapped_column(String(36), ForeignKey("seat_pools.id"), nullable=False)
    student_id: Mapped[str]           = mapped_column(String(36), ForeignKey("students.id"), unique=True, nullable=False)
    slot_no:    Mapped[int]           = mapped_column(Integer, nullable=False)
    over_by:    Mapped[int]           = mapped_column(Integer, default=0)   # >0 means breach
    claimed_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=now_utc)

    pool:    Mapped["SeatPool"] = relationship("SeatPool", back_populates="claims")
    student: Mapped["Student"]  = relationship("Student", back_populates="seat_claim")


# ── Submission (batch) ────────────────────────────────────────────
class Submission(Base):
    __tablename__ = "submissions"

    id:             Mapped[str]      = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str]      = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    batch_id:       Mapped[str]      = mapped_column(String(50), unique=True, nullable=False)
    idempotency_key:Mapped[str]      = mapped_column(String(100), unique=True, nullable=False)
    total_rows:     Mapped[int]      = mapped_column(Integer, default=0)
    accepted:       Mapped[int]      = mapped_column(Integer, default=0)
    rejected:       Mapped[int]      = mapped_column(Integer, default=0)
    held:           Mapped[int]      = mapped_column(Integer, default=0)
    status:         Mapped[str]      = mapped_column(String(30), default="PROCESSING")
    policy_version: Mapped[int]      = mapped_column(Integer, default=7)
    error_report:   Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    submitted_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    completed_at:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution", back_populates="submissions")


# ── Case ──────────────────────────────────────────────────────────
class Case(Base):
    __tablename__ = "cases"

    id:              Mapped[str]           = mapped_column(String(36), primary_key=True, default=new_uuid)
    case_ref:        Mapped[str]           = mapped_column(String(20), unique=True, nullable=False, index=True)
    case_type:       Mapped[str]           = mapped_column(String(50), nullable=False)
    severity:        Mapped[str]           = mapped_column(String(10), nullable=False)   # LOW|MEDIUM|HIGH|CRITICAL
    institution_id:  Mapped[str]           = mapped_column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    subject_type:    Mapped[str]           = mapped_column(String(30), nullable=False)
    subject_id:      Mapped[str]           = mapped_column(String(36), nullable=False)
    reason_codes:    Mapped[list]          = mapped_column(JSON, default=list)
    description:     Mapped[str]           = mapped_column(Text, nullable=False)
    status:          Mapped[str]           = mapped_column(String(30), default="Open")
    assigned_to:     Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    outcome:         Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rationale:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sla_due_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)
    opened_at:       Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=now_utc)
    closed_at:       Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution", back_populates="cases")


# ── Credential ────────────────────────────────────────────────────
class Credential(Base):
    __tablename__ = "credentials"

    id:          Mapped[str]           = mapped_column(String(36), primary_key=True, default=new_uuid)
    cred_id:     Mapped[str]           = mapped_column(String(100), unique=True, nullable=False, index=True)
    student_id:  Mapped[str]           = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    purpose:     Mapped[str]           = mapped_column(String(50), nullable=False)
    fields:      Mapped[list]          = mapped_column(JSON, nullable=False)
    claims:      Mapped[dict]          = mapped_column(JSON, nullable=False)
    signature:   Mapped[str]           = mapped_column(String(255), nullable=False)
    issued_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=now_utc)
    expires_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)
    revoked:     Mapped[bool]          = mapped_column(Boolean, default=False)
    revoked_at:  Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    used:        Mapped[bool]          = mapped_column(Boolean, default=False)
    used_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student:     Mapped["Student"]          = relationship("Student", back_populates="credentials")
    access_logs: Mapped[list["AccessLog"]]  = relationship("AccessLog", back_populates="credential")


# ── Access Log ────────────────────────────────────────────────────
class AccessLog(Base):
    __tablename__ = "access_logs"

    id:            Mapped[str]      = mapped_column(String(36), primary_key=True, default=new_uuid)
    credential_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("credentials.id"), nullable=True)
    student_id:    Mapped[str]      = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    verifier_id:   Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    verifier_name: Mapped[str]      = mapped_column(String(255), nullable=False)
    purpose:       Mapped[str]      = mapped_column(String(50), nullable=False)
    outcome:       Mapped[str]      = mapped_column(String(20), nullable=False)   # VALID|REVOKED|EXPIRED|DENIED
    fields_shared: Mapped[list]     = mapped_column(JSON, default=list)
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    credential: Mapped[Optional["Credential"]] = relationship("Credential", back_populates="access_logs")


# ── Audit Event ───────────────────────────────────────────────────
class AuditEvent(Base):
    __tablename__ = "audit_events"

    id:             Mapped[str]      = mapped_column(String(36), primary_key=True, default=new_uuid)
    chain_id:       Mapped[int]      = mapped_column(Integer, nullable=False, index=True)
    seq:            Mapped[int]      = mapped_column(BigInteger, nullable=False)
    actor:          Mapped[str]      = mapped_column(String(255), nullable=False)
    actor_type:     Mapped[str]      = mapped_column(String(20), nullable=False)
    action:         Mapped[str]      = mapped_column(String(100), nullable=False, index=True)
    entity:         Mapped[str]      = mapped_column(String(50), nullable=False)
    entity_id:      Mapped[str]      = mapped_column(String(100), nullable=False)
    payload:        Mapped[dict]     = mapped_column(JSON, nullable=False)
    payload_digest: Mapped[str]      = mapped_column(String(64), nullable=False)
    prev_hash:      Mapped[str]      = mapped_column(String(64), nullable=False)
    this_hash:      Mapped[str]      = mapped_column(String(64), nullable=False)
    created_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    __table_args__ = (
        UniqueConstraint("chain_id", "seq", name="uq_audit_chain_seq"),
        Index("ix_audit_entity", "entity", "entity_id"),
    )


# ── Verifier ──────────────────────────────────────────────────────
class Verifier(Base):
    __tablename__ = "verifiers"

    id:                    Mapped[str]      = mapped_column(String(36), primary_key=True, default=new_uuid)
    name:                  Mapped[str]      = mapped_column(String(255), nullable=False)
    verifier_type:         Mapped[str]      = mapped_column(String(50), nullable=False)
    email:                 Mapped[str]      = mapped_column(String(255), unique=True, nullable=False)
    api_key_hash:          Mapped[str]      = mapped_column(String(255), nullable=False)
    status:                Mapped[str]      = mapped_column(String(20), default="PENDING")
    purposes_allowed:      Mapped[list]     = mapped_column(JSON, default=list)
    quota_daily:           Mapped[int]      = mapped_column(Integer, default=50)
    verifications_today:   Mapped[int]      = mapped_column(Integer, default=0)
    total_verifications:   Mapped[int]      = mapped_column(Integer, default=0)
    registered_at:         Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_active_at:        Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
