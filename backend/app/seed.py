"""
Synthetic data seeder — populates the database with realistic demo data.
Run: python -m app.seed
"""
import random
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from .core.database import SessionLocal, engine, Base
from .models import (
    User, Institution, SeatPool, Person, Student, SeatClaim,
    Submission, Case, Credential, AccessLog, AuditEvent, Verifier,
)
from .core.security import hash_password
from .adapters.apaar_mock import generate_apaar_id, seed_known_apaar, generate_ppid

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

STATES = [
    ("Maharashtra", "Mumbai", "West"), ("Karnataka", "Bengaluru", "South"),
    ("Telangana", "Hyderabad", "South"), ("West Bengal", "Kolkata", "East"),
    ("Gujarat", "Nadiad", "West"), ("Tamil Nadu", "Chennai", "South"),
    ("Uttar Pradesh", "Kanpur", "North"), ("Rajasthan", "Jaipur", "North"),
]
INST_TYPES = ["Private", "Government", "NIT", "IIT"]
PROGRAMMES = ["B.Tech CSE", "B.Tech ECE", "B.Tech Mech", "B.Tech Civil", "M.Tech AI", "M.Tech VLSI", "B.Tech IT", "B.Tech Chem"]
POOLS = [("REGULAR", 60), ("NRI", 9), ("OCI", 3), ("SUPERNUMERARY", 3), ("FN", 3)]
FIRST_NAMES = ["Arjun","Meera","Rahul","Sneha","Omar","Priya","Kiran","Ananya","Vikram","Nisha","Tanmay","Lakshmi",
              "Rohan","Sneha","Aditya","Pooja","Karan","Divya","Manish","Riya","Sahil","Neha","Amit","Kavya",
              "Raj","Sneha","Yash","Isha","Dhruv","Anjali"]
LAST_NAMES = ["Sharma","Patel","Verma","Kulkarni","Al-Hassan","Menon","Reddy","Roy","Joshi","Gupta","Deshpande","Iyer",
             "Nair","Singh","Kumar","Das","Pillai","Shah","Mehta","Rao"]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_dob():
    y = random.randint(2002, 2006)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return f"{y:04d}-{m:02d}-{d:02d}"

def random_phone():
    return f"+91-98{random.randint(10000000,99999999)}"


def seed_all(db: Session, num_institutions: int = 8, students_per_inst: int = 12):
    """Seed the full database."""
    print("Seeding database...")

    # ── Create tables ──
    Base.metadata.create_all(bind=engine)

    # ── Institutions ──
    institutions = []
    for i, (state, district, region) in enumerate(STATES[:num_institutions]):
        inst_type = random.choice(INST_TYPES)
        inst = Institution(
            id=f"INST-{state[:2].upper()}-{i+1:04d}",
            name=f"Demo Institute of Technology, {district}",
            aicte_code=f"AICTE-{i+1:04d}",
            state=state, district=district, region=region,
            inst_type=inst_type,
            status="ACTIVE",
            integrity_band=random.choices(["A","B","C","D"], weights=[3,4,2,1])[0],
            integrity_score=random.randint(45, 99),
        )
        db.add(inst)
        institutions.append(inst)
    db.flush()

    # ── Users ──
    # Student user
    stu_person = Person(full_name="Arjun Sharma", apaar_id="1234-5678-9012", dob="2004-05-15", gender="Male", phone="+91-9876543210", trust_level=3)
    db.add(stu_person)
    db.flush()
    seed_known_apaar("1234-5678-9012", "Arjun Sharma", "2004-05-15", "photo_hash_demo")

    inst0 = institutions[0]
    stu = Student(
        id="STU-001", masked_id="STU-***-4821", person_id=stu_person.id,
        institution_id=inst0.id, programme="B.Tech CSE", academic_year="2026-27",
        pool_code="REGULAR", status="ENROLLED", hold_state="NONE", trust_level=3,
        risk_score=12, admission_date="2026-08-01",
    )
    db.add(stu)

    db.add(User(
        id="U-STU-001", email="arjun@demo.edu", hashed_password=hash_password("demo1234"),
        full_name="Arjun Sharma", role="student", student_id="STU-001",
    ))

    # Institution admin user
    db.add(User(
        id="U-INST-001", email="admin@demo.edu", hashed_password=hash_password("demo1234"),
        full_name="Dr. Priya Nair", role="institution", institution_id=inst0.id,
    ))

    # Officer user
    db.add(User(
        id="U-OFCR-001", email="officer@aicte.gov", hashed_password=hash_password("demo1234"),
        full_name="Shri Rajesh Kumar", role="officer",
    ))

    # ── Seat pools per institution ──
    for inst in institutions:
        for prog in PROGRAMMES[:4]:  # 4 programmes per inst
            for pool_code, cap in POOLS:
                if pool_code in ("NRI", "OCI", "FN") and random.random() > 0.3:
                    continue  # not all pools for all programmes
                pool = SeatPool(
                    institution_id=inst.id, programme=prog, pool_code=pool_code,
                    academic_year="2026-27", approved_intake=cap,
                    claimed=random.randint(0, cap), status="OK",
                )
                db.add(pool)
    db.flush()

    # ── Students ──
    student_count = 1
    for inst in institutions:
        for _ in range(students_per_inst):
            name = random_name()
            dob = random_dob()
            apaar_id = generate_apaar_id() if random.random() > 0.1 else None
            ppid = generate_ppid() if not apaar_id else None

            person = Person(
                full_name=name, apaar_id=apaar_id, ppid=ppid, dob=dob,
                gender=random.choice(["Male","Female"]),
                phone=random_phone(),
                trust_level=random.choices([0,1,2,3,4], weights=[1,2,4,3,1])[0],
            )
            db.add(person)
            db.flush()

            if apaar_id:
                seed_known_apaar(apaar_id, name, dob, "photo_hash")

            prog = random.choice(PROGRAMMES)
            pool_code = random.choices(["REGULAR","NRI","OCI","FN"], weights=[70,10,5,15])[0]

            student = Student(
                id=f"STU-{student_count:03d}",
                masked_id=f"STU-***-{random.randint(1000,9999)}",
                person_id=person.id,
                institution_id=inst.id,
                programme=prog,
                academic_year="2026-27",
                pool_code=pool_code,
                status=random.choices(["ENROLLED","CONTINUING","ADMITTED","WITHDRAWN"], weights=[60,20,15,5])[0],
                hold_state=random.choices(["NONE","CONFLICT_HOLD","IDENTITY_HOLD"], weights=[90,5,5])[0],
                trust_level=person.trust_level,
                risk_score=random.randint(0, 80),
                admission_date="2026-08-01",
            )
            db.add(student)
            student_count += 1

    # ── Verifier ──
    db.add(Verifier(
        id="VFR-001", name="TCS Recruitment", verifier_type="Employer",
        email="verify@tcs.com", api_key_hash=hash_password("tcs_api_key"),
        status="ACTIVE", purposes_allowed=["EMPLOYMENT","BACKGROUND_CHECK"],
        quota_daily=100, verifications_today=14, total_verifications=3420,
    ))
    db.add(Verifier(
        id="VFR-002", name="Infosys HR Verification", verifier_type="Employer",
        email="hr-verify@infosys.com", api_key_hash=hash_password("infosys_api_key"),
        status="ACTIVE", purposes_allowed=["EMPLOYMENT"],
        quota_daily=80, verifications_today=7, total_verifications=1890,
    ))

    # ── Cases ──
    case_data = [
        ("DUP_ENROLMENT","HIGH","LOCK_VIOLATION,APAAR_CONFLICT","Student has active full-time enrolment at two institutions."),
        ("INTAKE_BREACH","HIGH","POOL_OVER_CAP","REGULAR pool exceeded approved intake by 34 records."),
        ("DATA_MISMATCH","MEDIUM","NAME_DOB_MISMATCH,APAAR_VERIFY_FAIL","Student name differs from APAAR registry. Similarity: 0.71."),
        ("DECLARATION_MISMATCH","MEDIUM","DECLARED_VS_DERIVED_GAP","Declared enrolment differs from derived count by 68."),
        ("POSSIBLE_SAME_PERSON","MEDIUM","IDENTITY_GRAPH_MATCH,SHARED_CONTACT","Two records share guardian contact and similar names."),
    ]
    for i, (ctype, sev, codes, desc) in enumerate(case_data[:3]):
        inst = institutions[i % len(institutions)]
        db.add(Case(
            id=f"CASE-{i+1:04d}", case_ref=f"C-{i+1:042}", case_type=ctype, severity=sev,
            institution_id=inst.id, subject_type="student", subject_id=f"STU-{i+1:03d}",
            reason_codes=codes.split(","), description=desc,
            status=random.choice(["Open","UnderReview","AwaitingInstitution"]),
            assigned_to="Shri Rajesh Kumar",
            sla_due_at=datetime.now(timezone.utc) + timedelta(days=random.randint(1,7)),
            opened_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1,10)),
        ))

    # ── Audit events ──
    prev_hash = "0" * 64
    for i in range(5):
        payload = {"action": ["ENROLMENT_CREATED","IDENTITY_VERIFIED","SEAT_CLAIMED","TRUST_UPDATED","BATCH_SUBMITTED"][i], "entity_id": f"STU-{i+1:03d}"}
        import json
        raw = prev_hash + json.dumps(payload, sort_keys=True)
        this_hash = hashlib.sha256(raw.encode()).hexdigest()
        db.add(AuditEvent(
            id=f"AUD-{i+1:04d}", chain_id=1, seq=i+1,
            actor="System", actor_type="system",
            action=payload["action"], entity="enrolment", entity_id=payload["entity_id"],
            payload=payload,
            payload_digest=hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:16],
            prev_hash=prev_hash, this_hash=this_hash,
        ))
        prev_hash = this_hash

    # ── Seed demo credential ──
    cred = Credential(
        id="CRED-DEMO", cred_id="DEMO", student_id="STU-001",
        purpose="EMPLOYMENT",
        fields=["degree","institution","year","status"],
        claims={
            "degree": "B.Tech Computer Science & Engineering",
            "institution": "Demo Institute of Technology, Mumbai",
            "year": "2026-27",
            "status": "ENROLLED",
        },
        signature="demo_sig",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(cred)

    db.commit()
    print(f"Seeded: {len(institutions)} institutions, {student_count-1} students, 3 cases, 5 audit events, 1 demo credential, 2 verifiers")
    print("Login credentials:")
    print("  Student:     arjun@demo.edu / demo1234")
    print("  Institution: admin@demo.edu / demo1234")
    print("  Officer:     officer@aicte.gov / demo1234")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
