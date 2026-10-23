from typing import List, Dict, Any, Optional
from app.audit.chain import AuditChainEngine
from app.engine.policy_engine import PolicyEngine
from app.ml.risk_scorer import StudentRiskScorer
from app.ml.identity_resolver import IdentityResolutionEngine

class AppState:
    def __init__(self):
        self.audit_engine = AuditChainEngine()
        self.policy_engine = PolicyEngine()
        self.risk_scorer = StudentRiskScorer()
        self.identity_resolver = IdentityResolutionEngine()
        self._init_data()

    def _init_data(self):
        # 1. Institutions
        self.institutions = [
            {
                "id": "INST-MH-0042",
                "name": "Shri Institute of Engineering & Technology",
                "state": "Maharashtra",
                "district": "Mumbai",
                "region": "West",
                "type": "Private",
                "status": "ACTIVE",
                "approvedIntake": 240,
                "enrolledCount": 231,
                "verifiedCount": 198,
                "openCases": 3,
                "integrityBand": "B",
                "integrityScore": 82,
                "lastSubmission": "2026-10-18",
                "programmes": [
                    {"code": "CSE", "name": "B.Tech Computer Science", "approved": 120, "enrolled": 122, "status": "BREACH"},
                    {"code": "ECE", "name": "B.Tech Electronics & Comm", "approved": 60, "enrolled": 58, "status": "OK"},
                    {"code": "MECH", "name": "B.Tech Mechanical Eng", "approved": 60, "enrolled": 51, "status": "OK"}
                ]
            },
            {
                "id": "INST-KA-0021",
                "name": "RV College of Engineering",
                "state": "Karnataka",
                "district": "Bengaluru",
                "region": "South",
                "type": "Private",
                "status": "ACTIVE",
                "approvedIntake": 480,
                "enrolledCount": 462,
                "verifiedCount": 451,
                "openCases": 1,
                "integrityBand": "A",
                "integrityScore": 94,
                "lastSubmission": "2026-10-15",
                "programmes": [
                    {"code": "CSE", "name": "B.Tech Computer Science", "approved": 180, "enrolled": 178, "status": "OK"},
                    {"code": "ECE", "name": "B.Tech Electronics & Comm", "approved": 120, "enrolled": 118, "status": "OK"},
                    {"code": "ISE", "name": "B.Tech Information Science", "approved": 120, "enrolled": 114, "status": "OK"},
                    {"code": "MECH", "name": "B.Tech Mechanical Eng", "approved": 60, "enrolled": 52, "status": "OK"}
                ]
            },
            {
                "id": "INST-TS-0015",
                "name": "JNTU College of Engineering Hyderabad",
                "state": "Telangana",
                "district": "Hyderabad",
                "region": "South",
                "type": "Government",
                "status": "ACTIVE",
                "approvedIntake": 360,
                "enrolledCount": 394,
                "verifiedCount": 310,
                "openCases": 7,
                "integrityBand": "C",
                "integrityScore": 61,
                "lastSubmission": "2026-10-10",
                "programmes": [
                    {"code": "CSE", "name": "B.Tech Computer Science", "approved": 120, "enrolled": 142, "status": "BREACH"},
                    {"code": "IT", "name": "B.Tech Information Tech", "approved": 120, "enrolled": 132, "status": "BREACH"},
                    {"code": "EEE", "name": "B.Tech Electrical & Electronics", "approved": 120, "enrolled": 120, "status": "OK"}
                ]
            },
            {
                "id": "INST-WB-0009",
                "name": "Jadavpur University",
                "state": "West Bengal",
                "district": "Kolkata",
                "region": "East",
                "type": "Government",
                "status": "ACTIVE",
                "approvedIntake": 300,
                "enrolledCount": 287,
                "verifiedCount": 280,
                "openCases": 0,
                "integrityBand": "A",
                "integrityScore": 97,
                "lastSubmission": "2026-10-20",
                "programmes": [
                    {"code": "CSE", "name": "B.Tech Computer Science", "approved": 100, "enrolled": 98, "status": "OK"},
                    {"code": "ETC", "name": "B.Tech Electronics & Telecom", "approved": 100, "enrolled": 95, "status": "OK"},
                    {"code": "CHEM", "name": "B.Tech Chemical Eng", "approved": 100, "enrolled": 94, "status": "OK"}
                ]
            },
            {
                "id": "INST-GJ-0037",
                "name": "Dharmsinh Desai Institute of Technology",
                "state": "Gujarat",
                "district": "Nadiad",
                "region": "West",
                "type": "Private",
                "status": "ACTIVE",
                "approvedIntake": 180,
                "enrolledCount": 175,
                "verifiedCount": 141,
                "openCases": 2,
                "integrityBand": "B",
                "integrityScore": 78,
                "lastSubmission": "2026-10-12",
                "programmes": [
                    {"code": "IT", "name": "B.Tech Information Tech", "approved": 90, "enrolled": 89, "status": "OK"},
                    {"code": "CIVIL", "name": "B.Tech Civil Eng", "approved": 90, "enrolled": 86, "status": "OK"}
                ]
            },
            {
                "id": "INST-TN-0088",
                "name": "Anna University",
                "state": "Tamil Nadu",
                "district": "Chennai",
                "region": "South",
                "type": "Government",
                "status": "ACTIVE",
                "approvedIntake": 600,
                "enrolledCount": 598,
                "verifiedCount": 590,
                "openCases": 0,
                "integrityBand": "A",
                "integrityScore": 99,
                "lastSubmission": "2026-10-21",
                "programmes": [
                    {"code": "CSE", "name": "B.Tech Computer Science", "approved": 240, "enrolled": 240, "status": "OK"},
                    {"code": "ECE", "name": "B.Tech Electronics & Comm", "approved": 180, "enrolled": 179, "status": "OK"},
                    {"code": "VLSI", "name": "M.Tech VLSI Design", "approved": 180, "enrolled": 179, "status": "OK"}
                ]
            },
            {
                "id": "INST-UP-0055",
                "name": "Harcourt Butler Technical University",
                "state": "Uttar Pradesh",
                "district": "Kanpur",
                "region": "North",
                "type": "Government",
                "status": "ACTIVE",
                "approvedIntake": 420,
                "enrolledCount": 488,
                "verifiedCount": 312,
                "openCases": 12,
                "integrityBand": "D",
                "integrityScore": 44,
                "lastSubmission": "2026-09-30",
                "programmes": [
                    {"code": "CSE", "name": "B.Tech Computer Science", "approved": 120, "enrolled": 158, "status": "BREACH"},
                    {"code": "IT", "name": "B.Tech Information Tech", "approved": 120, "enrolled": 140, "status": "BREACH"},
                    {"code": "MECH", "name": "B.Tech Mechanical Eng", "approved": 180, "enrolled": 190, "status": "BREACH"}
                ]
            },
            {
                "id": "INST-RJ-0018",
                "name": "Malaviya National Institute of Technology",
                "state": "Rajasthan",
                "district": "Jaipur",
                "region": "North",
                "type": "NIT",
                "status": "ACTIVE",
                "approvedIntake": 360,
                "enrolledCount": 358,
                "verifiedCount": 350,
                "openCases": 0,
                "integrityBand": "A",
                "integrityScore": 96,
                "lastSubmission": "2026-10-19",
                "programmes": [
                    {"code": "CSE", "name": "B.Tech Computer Science", "approved": 120, "enrolled": 120, "status": "OK"},
                    {"code": "ECE", "name": "B.Tech Electronics & Comm", "approved": 120, "enrolled": 119, "status": "OK"},
                    {"code": "EE", "name": "B.Tech Electrical Eng", "approved": 120, "enrolled": 119, "status": "OK"}
                ]
            }
        ]

        # 2. Students
        self.students = [
            {
                "id": "s1", "maskedId": "STU-***-4821", "name": "Arjun Sharma", "apaarId": "1234-5678-9012",
                "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "programme": "B.Tech CSE",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "NONE", "trustLevel": 3,
                "admissionDate": "2026-08-01", "poolCode": "REGULAR", "riskScore": 12, "lastUpdated": "2026-10-10",
                "gender": "Male", "category": "General", "marksPercentile": 94.2,
                "riskFactors": [{"factor": "Verified Cohort Baseline", "impact": "0 pts", "severity": "INFO", "detail": "All credentials aligned."}]
            },
            {
                "id": "s2", "maskedId": "STU-***-3317", "name": "Meera Patel", "apaarId": "2345-6789-0123",
                "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "programme": "B.Tech ECE",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "NONE", "trustLevel": 2,
                "admissionDate": "2026-08-03", "poolCode": "REGULAR", "riskScore": 8, "lastUpdated": "2026-10-12",
                "gender": "Female", "category": "OBC", "marksPercentile": 88.5
            },
            {
                "id": "s3", "maskedId": "STU-***-7749", "name": "Rahul Verma", "apaarId": "3456-7890-1234",
                "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "programme": "B.Tech Mech",
                "academicYear": "2026-27", "status": "ADMITTED", "holdState": "CONFLICT_HOLD", "trustLevel": 1,
                "admissionDate": "2026-08-10", "poolCode": "REGULAR", "riskScore": 74, "lastUpdated": "2026-10-18",
                "gender": "Male", "category": "General", "marksPercentile": 79.0,
                "crossEnrolments": [
                    {"institutionName": "RV College Bengaluru", "programme": "B.Tech Mechanical", "admissionDate": "2026-08-08", "status": "ACTIVE"}
                ],
                "riskFactors": [
                    {"factor": "Simultaneous Multi-Institution Enrolment", "impact": "+45 pts", "severity": "CRITICAL", "detail": "Active claim concurrently found at RV College Bengaluru."},
                    {"factor": "Low Trust Tier (L1)", "impact": "+15 pts", "severity": "MEDIUM", "detail": "Unverified against central matriculation registry."}
                ]
            },
            {
                "id": "s4", "maskedId": "STU-***-2205", "name": "Sneha Kulkarni", "apaarId": "4567-8901-2345",
                "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "programme": "M.Tech AI",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "NONE", "trustLevel": 3,
                "admissionDate": "2026-08-05", "poolCode": "REGULAR", "riskScore": 5, "lastUpdated": "2026-10-14",
                "gender": "Female", "category": "General", "marksPercentile": 96.0
            },
            {
                "id": "s5", "maskedId": "STU-***-9934", "name": "Omar Al-Hassan", "apaarId": None,
                "institutionId": "INST-KA-0021", "institutionName": "RV College Bengaluru", "programme": "B.Tech CSE",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "IDENTITY_HOLD", "trustLevel": 1,
                "admissionDate": "2026-09-01", "poolCode": "FN", "riskScore": 45, "lastUpdated": "2026-10-05",
                "gender": "Male", "category": "Foreign National", "marksPercentile": 82.0,
                "riskFactors": [
                    {"factor": "Missing APAAR Registry ID", "impact": "+25 pts", "severity": "HIGH", "detail": "International student assigned provisional PPID-9934."},
                    {"factor": "Late Admission Waiver", "impact": "+20 pts", "severity": "MEDIUM", "detail": "Admitted after regular semester orientation window."}
                ]
            },
            {
                "id": "s6", "maskedId": "STU-***-6612", "name": "Priya Menon", "apaarId": "5678-9012-3456",
                "institutionId": "INST-KA-0021", "institutionName": "RV College Bengaluru", "programme": "B.Tech CSE",
                "academicYear": "2026-27", "status": "CONTINUING", "holdState": "NONE", "trustLevel": 4,
                "admissionDate": "2025-08-01", "poolCode": "REGULAR", "riskScore": 3, "lastUpdated": "2026-09-30",
                "gender": "Female", "category": "General", "marksPercentile": 98.5
            },
            {
                "id": "s7", "maskedId": "STU-***-8801", "name": "Kiran Reddy", "apaarId": "6789-0123-4567",
                "institutionId": "INST-TS-0015", "institutionName": "JNTU Hyderabad", "programme": "B.Tech IT",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "NONE", "trustLevel": 2,
                "admissionDate": "2026-08-15", "poolCode": "NRI", "riskScore": 18, "lastUpdated": "2026-10-09",
                "gender": "Male", "category": "NRI", "marksPercentile": 84.0
            },
            {
                "id": "s8", "maskedId": "STU-***-1123", "name": "Ananya Roy", "apaarId": "7890-1234-5678",
                "institutionId": "INST-WB-0009", "institutionName": "Jadavpur University", "programme": "B.Tech Chem",
                "academicYear": "2026-27", "status": "WITHDRAWN", "holdState": "NONE", "trustLevel": 2,
                "admissionDate": "2026-08-02", "poolCode": "REGULAR", "riskScore": 0, "lastUpdated": "2026-09-20",
                "gender": "Female", "category": "General", "marksPercentile": 91.0
            },
            {
                "id": "s9", "maskedId": "STU-***-5571", "name": "Vikram Joshi", "apaarId": "8901-2345-6789",
                "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "programme": "B.Tech CSE",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "NONE", "trustLevel": 3,
                "admissionDate": "2026-08-04", "poolCode": "REGULAR", "riskScore": 22, "lastUpdated": "2026-10-15",
                "gender": "Male", "category": "General", "marksPercentile": 89.2
            },
            {
                "id": "s10", "maskedId": "STU-***-4490", "name": "Nisha Gupta", "apaarId": "9012-3456-7890",
                "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "programme": "B.Tech ECE",
                "academicYear": "2026-27", "status": "CONTINUING", "holdState": "NONE", "trustLevel": 3,
                "admissionDate": "2025-08-01", "poolCode": "REGULAR", "riskScore": 7, "lastUpdated": "2026-10-01",
                "gender": "Female", "category": "General", "marksPercentile": 92.5
            },
            {
                "id": "s11", "maskedId": "STU-***-3382", "name": "Tanmay Deshpande", "apaarId": "0123-4567-8901",
                "institutionId": "INST-GJ-0037", "institutionName": "DDIT Nadiad", "programme": "B.Tech Civil",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "NONE", "trustLevel": 2,
                "admissionDate": "2026-08-10", "poolCode": "REGULAR", "riskScore": 14, "lastUpdated": "2026-10-11",
                "gender": "Male", "category": "General", "marksPercentile": 80.0
            },
            {
                "id": "s12", "maskedId": "STU-***-7761", "name": "Lakshmi Iyer", "apaarId": "1234-5678-2222",
                "institutionId": "INST-TN-0088", "institutionName": "Anna University", "programme": "M.Tech VLSI",
                "academicYear": "2026-27", "status": "ENROLLED", "holdState": "NONE", "trustLevel": 4,
                "admissionDate": "2026-08-20", "poolCode": "REGULAR", "riskScore": 2, "lastUpdated": "2026-10-20",
                "gender": "Female", "category": "General", "marksPercentile": 99.1
            }
        ]

        # 3. Cases
        self.cases = [
            {
                "id": "C-0042",
                "caseType": "DUP_ENROLMENT",
                "severity": "CRITICAL",
                "institutionId": "INST-MH-0042",
                "institutionName": "SIET Mumbai",
                "subjectType": "student",
                "subjectId": "s3",
                "reasonCodes": ["LOCK_VIOLATION", "APAAR_CONFLICT"],
                "status": "UnderReview",
                "assignedTo": "Shri Rajesh Kumar",
                "slaDueAt": "2026-10-24",
                "openedAt": "2026-10-18",
                "description": "Student has active full-time enrolment at SIET Mumbai and RV College Bengaluru. Single-seat lock holding new claim pending officer mediation.",
                "evidencePack": {
                    "matchedStudent": "Rahul Verma",
                    "studentRef": "STU-***-7749",
                    "competingInstitution": "RV College Bengaluru",
                    "apaarId": "3456-7890-1234",
                    "admissionGapDays": 2,
                    "recommendedAction": "Require student declaration or surrender seat at RV College."
                }
            },
            {
                "id": "C-0039",
                "caseType": "INTAKE_BREACH",
                "severity": "CRITICAL",
                "institutionId": "INST-TS-0015",
                "institutionName": "JNTU Hyderabad",
                "subjectType": "seat_pool",
                "subjectId": "REGULAR-2026",
                "reasonCodes": ["POOL_OVER_CAP", "EXCESS_ADMISSION"],
                "status": "AwaitingInstitution",
                "assignedTo": "Shri Rajesh Kumar",
                "slaDueAt": "2026-10-25",
                "openedAt": "2026-10-10",
                "description": "REGULAR pool exceeded approved intake by 34 records. Institution must provide AICTE justification or de-register excess unapproved students.",
                "evidencePack": {
                    "approvedIntake": 360,
                    "claimedIntake": 394,
                    "excessCount": 34,
                    "breachedProgrammes": ["B.Tech CSE (+22 seats)", "B.Tech IT (+12 seats)"]
                }
            },
            {
                "id": "C-0036",
                "caseType": "DATA_MISMATCH",
                "severity": "MEDIUM",
                "institutionId": "INST-GJ-0037",
                "institutionName": "DDIT Nadiad",
                "subjectType": "student",
                "subjectId": "s11",
                "reasonCodes": ["NAME_DOB_MISMATCH", "APAAR_VERIFY_FAIL"],
                "status": "Open",
                "assignedTo": "Shri Rajesh Kumar",
                "slaDueAt": "2026-10-26",
                "openedAt": "2026-10-14",
                "description": "Student name in submission (Tanmay Deshpande) differs from APAAR registry (Tanmay Desh.). Jaro-Winkler similarity: 0.78.",
                "evidencePack": {
                    "submittedName": "Tanmay Deshpande",
                    "registryName": "Tanmay Desh.",
                    "jaroWinkler": 0.78,
                    "dobMatch": True
                }
            },
            {
                "id": "C-0031",
                "caseType": "DECLARATION_MISMATCH",
                "severity": "HIGH",
                "institutionId": "INST-UP-0055",
                "institutionName": "HBTU Kanpur",
                "subjectType": "institution",
                "subjectId": "INST-UP-0055",
                "reasonCodes": ["DECLARED_VS_DERIVED_GAP"],
                "status": "Escalated",
                "assignedTo": "Shri Rajesh Kumar",
                "slaDueAt": "2026-10-23",
                "openedAt": "2026-09-28",
                "description": "Declared enrolment (420) differs from student-row derived count (488) by 68. Ghost-student or off-record batch entries detected.",
                "evidencePack": {
                    "declaredTotal": 420,
                    "derivedRowsCount": 488,
                    "gapDiscrepancy": 68
                }
            },
            {
                "id": "C-0028",
                "caseType": "POSSIBLE_SAME_PERSON",
                "severity": "MEDIUM",
                "institutionId": "INST-MH-0042",
                "institutionName": "SIET Mumbai",
                "subjectType": "student",
                "subjectId": "s9",
                "reasonCodes": ["IDENTITY_GRAPH_MATCH", "SHARED_CONTACT"],
                "status": "Open",
                "assignedTo": "Shri Rajesh Kumar",
                "slaDueAt": "2026-10-28",
                "openedAt": "2026-10-16",
                "description": "Two records share identical guardian contact and similar names with slight transliteration difference. Possible duplicate identity.",
                "evidencePack": {
                    "recordA": "Vikram Joshi (SIET Mumbai)",
                    "recordB": "Vikram J Joshi (VJTI Mumbai)",
                    "contactMatch": "98201*****"
                }
            },
            {
                "id": "C-0021",
                "caseType": "ANOMALY",
                "severity": "LOW",
                "institutionId": "INST-TS-0015",
                "institutionName": "JNTU Hyderabad",
                "subjectType": "batch",
                "subjectId": "BATCH-2874",
                "reasonCodes": ["BULK_UPLOAD_SPIKE", "DEADLINE_BURST"],
                "status": "Resolved",
                "assignedTo": "Shri Rajesh Kumar",
                "slaDueAt": "2026-10-15",
                "openedAt": "2026-10-08",
                "closedAt": "2026-10-14",
                "outcome": "Resolved: Reviewed by officer. Institution confirmed legitimate pre-deadline upload. No sanction required.",
                "description": "Bulk upload of 180 records in final 24 hours before deadline. Anomaly score: 68/100."
            },
            {
                "id": "C-0018",
                "caseType": "INVALID_ID",
                "severity": "LOW",
                "institutionId": "INST-KA-0021",
                "institutionName": "RV College Bengaluru",
                "subjectType": "student",
                "subjectId": "s5",
                "reasonCodes": ["MISSING_APAAR", "PROVISIONAL_IDENTITY"],
                "status": "Open",
                "assignedTo": "Shri Rajesh Kumar",
                "slaDueAt": "2026-11-01",
                "openedAt": "2026-10-20",
                "description": "Foreign national student without APAAR. Provisional identity (PPID) assigned. Physical passport check required for L2 elevation."
            }
        ]

        # 4. Identity Graph Records
        self.identity_records = [
            {"id": "IR-001", "personId": "PID-4821", "name": "Arjun Sharma", "apaarId": "1234-5678-9012", "institution": "SIET Mumbai", "trustLevel": 3, "status": "VERIFIED"},
            {"id": "IR-002", "personId": "PID-7749", "name": "Rahul Verma", "apaarId": "3456-7890-1234", "institution": "SIET Mumbai", "trustLevel": 1, "status": "CONFLICT", "conflictType": "DUP_ENROLMENT", "matchScore": 99},
            {"id": "IR-003", "personId": "PID-9934", "name": "Omar Al-Hassan", "institution": "RV College Bengaluru", "trustLevel": 1, "status": "PROVISIONAL", "ppid": "PPID-9934"},
            {"id": "IR-004", "personId": "PID-6612", "name": "Priya Menon", "apaarId": "5678-9012-3456", "institution": "RV College Bengaluru", "trustLevel": 4, "status": "VERIFIED"},
            {"id": "IR-005", "personId": "PID-8801A", "name": "Kiran Reddy", "apaarId": "6789-0123-4567", "institution": "JNTU Hyderabad", "trustLevel": 2, "status": "VERIFIED"},
            {"id": "IR-006", "personId": "PID-8801B", "name": "Kiran Redy", "apaarId": "6789-0123-9999", "institution": "DDIT Nadiad", "trustLevel": 1, "status": "CANDIDATE", "conflictType": "POSSIBLE_SAME_PERSON", "matchScore": 78},
            {"id": "IR-007", "personId": "PID-5571", "name": "Vikram Joshi", "apaarId": "8901-2345-6789", "institution": "SIET Mumbai", "trustLevel": 3, "status": "VERIFIED"},
            {"id": "IR-008", "personId": "PID-2205", "name": "Sneha Kulkarni", "apaarId": "4567-8901-2345", "institution": "SIET Mumbai", "trustLevel": 3, "status": "VERIFIED"}
        ]

        # 5. Merge Journal
        self.merge_journal = [
            {
                "id": "MJ-001",
                "survivor": "PID-4821",
                "absorbed": "PID-4821B",
                "method": "APAAR_MATCH",
                "confidence": 0.97,
                "approvedBy": "Shri Rajesh Kumar",
                "mergedAt": "2026-09-12T10:00:00Z",
                "undoneAt": None,
                "reason": "Same person with stale provisional ID after APAAR registration."
            },
            {
                "id": "MJ-002",
                "survivor": "PID-6612",
                "absorbed": "PID-6612C",
                "method": "AUTO_MATCH",
                "confidence": 0.99,
                "approvedBy": "System",
                "mergedAt": "2026-08-20T14:30:00Z",
                "undoneAt": None,
                "reason": "Auto-merge: name match 0.99, DOB exact, APAAR confirmed."
            }
        ]

        # 6. Verifiers
        self.verifiers = [
            {
                "id": "VFR-001", "name": "TCS Recruitment Verification", "type": "Employer",
                "email": "verify@tcs.com", "status": "ACTIVE", "verificationsToday": 14,
                "quotaDaily": 100, "totalVerifications": 3420, "registeredOn": "2026-06-01",
                "lastActive": "2026-10-22", "purposesAllowed": ["EMPLOYMENT", "BACKGROUND_CHECK"]
            },
            {
                "id": "VFR-002", "name": "Infosys HR Verification Desk", "type": "Employer",
                "email": "hr-verify@infosys.com", "status": "ACTIVE", "verificationsToday": 7,
                "quotaDaily": 80, "totalVerifications": 1890, "registeredOn": "2026-07-15",
                "lastActive": "2026-10-21", "purposesAllowed": ["EMPLOYMENT"]
            },
            {
                "id": "VFR-003", "name": "NAAC Accreditation Assessment Body", "type": "Regulator",
                "email": "verify@naac.gov.in", "status": "ACTIVE", "verificationsToday": 2,
                "quotaDaily": 50, "totalVerifications": 210, "registeredOn": "2026-08-01",
                "lastActive": "2026-10-20", "purposesAllowed": ["ACCREDITATION", "REGULATORY"]
            },
            {
                "id": "VFR-004", "name": "State Education Dept. Maharashtra", "type": "Government",
                "email": "verify@education.mh.gov", "status": "ACTIVE", "verificationsToday": 1,
                "quotaDaily": 200, "totalVerifications": 88, "registeredOn": "2026-09-10",
                "lastActive": "2026-10-18", "purposesAllowed": ["REGULATORY", "SCHOLARSHIP"]
            },
            {
                "id": "VFR-005", "name": "QuickHire Background Checks Pvt Ltd", "type": "Employer",
                "email": "ops@quickhire.in", "status": "SUSPENDED", "verificationsToday": 0,
                "quotaDaily": 50, "totalVerifications": 440, "registeredOn": "2026-07-01",
                "lastActive": "2026-10-10", "purposesAllowed": ["EMPLOYMENT"]
            },
            {
                "id": "VFR-006", "name": "GlobalEdu Credentials Inc.", "type": "Education",
                "email": "verify@globaledu.com", "status": "PENDING", "verificationsToday": 0,
                "quotaDaily": 0, "totalVerifications": 0, "registeredOn": "2026-10-20",
                "lastActive": "—", "purposesAllowed": []
            }
        ]

        # 7. Verification Logs
        self.verification_logs = [
            {"id": "VL-001", "verifierId": "VFR-001", "verifierName": "TCS Recruitment", "purpose": "EMPLOYMENT", "outcome": "VALID", "fieldsReturned": ["degree", "year", "institution", "status"], "at": "2026-10-22T11:20:00Z", "consentRef": "CNS-7821"},
            {"id": "VL-002", "verifierId": "VFR-001", "verifierName": "TCS Recruitment", "purpose": "EMPLOYMENT", "outcome": "REVOKED", "fieldsReturned": [], "at": "2026-10-22T10:55:00Z", "consentRef": "CNS-7810"},
            {"id": "VL-003", "verifierId": "VFR-002", "verifierName": "Infosys HR Verification Desk", "purpose": "EMPLOYMENT", "outcome": "VALID", "fieldsReturned": ["degree", "institution", "status"], "at": "2026-10-21T14:30:00Z", "consentRef": "CNS-7745"},
            {"id": "VL-004", "verifierId": "VFR-003", "verifierName": "NAAC Accreditation Body", "purpose": "ACCREDITATION", "outcome": "VALID", "fieldsReturned": ["degree", "year", "institution"], "at": "2026-10-20T09:10:00Z", "consentRef": "CNS-7700"},
            {"id": "VL-005", "verifierId": "VFR-005", "verifierName": "QuickHire Background Checks", "purpose": "EMPLOYMENT", "outcome": "DENIED", "fieldsReturned": [], "at": "2026-10-10T16:44:00Z", "consentRef": "—"}
        ]

        # 8. Student Academic Documents & Credentials
        self.documents = [
            {"id": "d1", "studentId": "s1", "type": "APAAR ID", "name": "APAAR_Card_1234.pdf", "status": "VERIFIED", "uploadedAt": "2026-08-01T10:00:00Z", "verifiedAt": "2026-08-02T09:00:00Z", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "issuer": "UIDAI / Ministry of Education"},
            {"id": "d2", "studentId": "s1", "type": "Admission Letter", "name": "Admission_Letter_2026.pdf", "status": "VERIFIED", "uploadedAt": "2026-08-01T10:05:00Z", "verifiedAt": "2026-08-04T11:00:00Z", "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a", "issuer": "SIET Mumbai Registrar"},
            {"id": "d3", "studentId": "s1", "type": "Marksheet (Class 12)", "name": "HSC_Marksheet.pdf", "status": "VERIFIED", "uploadedAt": "2026-08-01T10:10:00Z", "verifiedAt": "2026-08-03T14:00:00Z", "sha256": "ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d", "issuer": "CBSE Board Examination"},
            {"id": "d4", "studentId": "s1", "type": "Category Certificate", "name": "Caste_Certificate.pdf", "status": "PENDING", "uploadedAt": "2026-09-15T08:00:00Z", "verifiedAt": None, "sha256": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e", "issuer": "Tehsildar Office Mumbai Suburban"},
            {"id": "d5", "studentId": "s1", "type": "Photo ID", "name": "Aadhar_Card.pdf", "status": "VERIFIED", "uploadedAt": "2026-08-01T10:15:00Z", "verifiedAt": "2026-08-02T09:30:00Z", "sha256": "b0a8a9a6860d5b5db305b0fcf05a4ec601556e432c6e76cf7cc5e2ca7099f7d0", "issuer": "UIDAI"},
            {"id": "d6", "studentId": "s1", "type": "Migration Certificate", "name": "Migration_Cert.pdf", "status": "UPLOADED", "uploadedAt": "2026-10-10T12:00:00Z", "verifiedAt": None, "sha256": "7c4a8d09ca3762af61e59520943dc26494f8941b52a1d279cf7349141f2e8412", "issuer": "State Board Higher Secondary"}
        ]

        # 9. Student Requests (Clarification & Correction)
        self.student_requests = [
            {
                "id": "R-001",
                "studentId": "s1",
                "type": "Clarification",
                "title": "Category Certificate — Pending Verification",
                "status": "Awaiting Review",
                "date": "2026-09-15",
                "detail": "Category certificate has been uploaded and is awaiting officer review."
            },
            {
                "id": "R-002",
                "studentId": "s1",
                "type": "Correction",
                "title": "Mobile number update request",
                "status": "Resolved",
                "date": "2026-08-02",
                "detail": "Mobile number updated successfully. Change recorded and audited."
            }
        ]

        # 10. Submissions (Institution batches)
        self.submissions = [
            {"id": "sub1", "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "batchId": "BATCH-2901", "submittedAt": "2026-10-18T09:22:00Z", "totalRows": 245, "accepted": 231, "rejected": 8, "held": 6, "status": "COMPLETED_WITH_ERRORS", "policyVersion": 7},
            {"id": "sub2", "institutionId": "INST-KA-0021", "institutionName": "RV College", "batchId": "BATCH-2899", "submittedAt": "2026-10-15T14:10:00Z", "totalRows": 480, "accepted": 462, "rejected": 18, "held": 0, "status": "COMPLETED", "policyVersion": 7},
            {"id": "sub3", "institutionId": "INST-TS-0015", "institutionName": "JNTU Hyderabad", "batchId": "BATCH-2874", "submittedAt": "2026-10-10T23:45:00Z", "totalRows": 400, "accepted": 382, "rejected": 4, "held": 14, "status": "COMPLETED_WITH_ERRORS", "policyVersion": 7},
            {"id": "sub4", "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "batchId": "BATCH-2850", "submittedAt": "2026-09-20T11:00:00Z", "totalRows": 180, "accepted": 175, "rejected": 3, "held": 2, "status": "COMPLETED_WITH_ERRORS", "policyVersion": 6},
            {"id": "sub5", "institutionId": "INST-MH-0042", "institutionName": "SIET Mumbai", "batchId": "BATCH-2810", "submittedAt": "2026-08-15T10:00:00Z", "totalRows": 120, "accepted": 120, "rejected": 0, "held": 0, "status": "COMPLETED", "policyVersion": 6}
        ]

        # 11. Integrity Checks (Institution Findings)
        self.integrity_checks = [
            {"id": "IC-001", "institutionId": "INST-MH-0042", "rule": "R1 · INTAKE_BREACH", "severity": "HIGH", "subject": "B.Tech CSE — REGULAR pool", "detail": "Claimed 62 against cap of 60. Over by 2.", "status": "OPEN", "raisedAt": "2026-10-18"},
            {"id": "IC-002", "institutionId": "INST-MH-0042", "rule": "R6 · NAME_DOB_MISMATCH", "severity": "MEDIUM", "subject": "STU-***-3382 (Tanmay D.)", "detail": "Name similarity 0.71. Manual match needed.", "status": "OPEN", "raisedAt": "2026-10-14"},
            {"id": "IC-003", "institutionId": "INST-MH-0042", "rule": "R1 · INTAKE_BREACH", "severity": "HIGH", "subject": "B.Tech CSE — NRI pool", "detail": "Claimed 11 against cap of 9. Over by 2.", "status": "OPEN", "raisedAt": "2026-10-18"},
            {"id": "IC-004", "institutionId": "INST-MH-0042", "rule": "R3 · SHARED_ATTRIBUTE", "severity": "MEDIUM", "subject": "Cluster of 3 students", "detail": "Same guardian contact across 3 records. Possible data entry error or family.", "status": "OPEN", "raisedAt": "2026-10-16"},
            {"id": "IC-005", "institutionId": "INST-MH-0042", "rule": "R12 · BATCH_ERROR_RATE", "severity": "LOW", "subject": "BATCH-2888", "detail": "Error rate 3.3% (6/180). Above 2% threshold.", "status": "RESOLVED", "raisedAt": "2026-10-12"}
        ]

# Global singleton
state = AppState()
