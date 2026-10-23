"""
Pydantic Models for APAAR AICTE Officer Portal
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

# --- Institution ---
class InstitutionModel(BaseModel):
    id: str
    name: str
    state: str
    district: str
    region: str
    type: str
    status: Literal['ACTIVE', 'INACTIVE', 'SUSPENDED']
    approvedIntake: int
    enrolledCount: int
    verifiedCount: int
    openCases: int
    integrityBand: Literal['A', 'B', 'C', 'D', 'E']
    integrityScore: int
    lastSubmission: str
    programmes: Optional[List[Dict[str, Any]]] = None

class InstitutionActionRequest(BaseModel):
    action: Literal['SHOW_CAUSE_NOTICE', 'FREEZE_ADMISSIONS', 'ORDER_REAUDIT']
    reason: str
    officerName: str

# --- Student / Enrolment ---
class StudentModel(BaseModel):
    id: str
    maskedId: str
    name: str
    apaarId: Optional[str] = None
    institutionId: str
    institutionName: str
    programme: str
    academicYear: str
    status: Literal['ADMITTED', 'ENROLLED', 'CONTINUING', 'TRANSFERRED', 'WITHDRAWN', 'CANCELLED', 'GRADUATED']
    holdState: Literal['NONE', 'CONFLICT_HOLD', 'IDENTITY_HOLD']
    trustLevel: int
    admissionDate: str
    poolCode: str
    riskScore: int
    lastUpdated: str
    gender: Optional[str] = 'Unspecified'
    category: Optional[str] = 'General'
    marksPercentile: Optional[float] = 85.0
    riskFactors: Optional[List[Dict[str, Any]]] = None
    crossEnrolments: Optional[List[Dict[str, Any]]] = None

class HoldToggleRequest(BaseModel):
    holdState: Literal['NONE', 'CONFLICT_HOLD', 'IDENTITY_HOLD']
    reason: Optional[str] = "Officer regulatory hold status adjustment."
    officerName: Optional[str] = "Shri Rajesh Kumar"


class RiskPredictRequest(BaseModel):
    age: float
    submissionDaysBeforeDeadline: float
    hasApaar: bool
    isMultiInstitutionClaim: bool
    poolMismatch: bool
    categoryCertVerified: bool

# --- Cases / Integrity Queue ---
class CaseModel(BaseModel):
    id: str
    caseType: Literal[
        'INTAKE_BREACH', 'DUP_ENROLMENT', 'POSSIBLE_SAME_PERSON',
        'INVALID_ID', 'DATA_MISMATCH', 'DECLARATION_MISMATCH',
        'ANOMALY', 'STALE_ACTIVE'
    ]
    severity: Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    institutionId: str
    institutionName: str
    subjectType: str
    subjectId: str
    reasonCodes: List[str]
    status: Literal[
        'Open', 'UnderReview', 'AwaitingInstitution', 'Resubmitted',
        'Escalated', 'Resolved', 'Appealed', 'Closed'
    ]
    assignedTo: Optional[str] = None
    slaDueAt: str
    openedAt: str
    closedAt: Optional[str] = None
    outcome: Optional[str] = None
    description: str
    evidencePack: Optional[Dict[str, Any]] = None

class OfficerDecisionRequest(BaseModel):
    decision: Literal['RESOLVE_NO_ISSUE', 'UPHOLD_BREACH', 'REQUEST_CLARIFICATION', 'ESCALATE_COMMITTEE', 'ENFORCE_PENALTY']
    rationale: str
    officerName: str

# --- Policy Studio ---
class PolicyRuleModel(BaseModel):
    id: str
    name: str
    description: str
    category: str
    currentStage: Literal['OBSERVE', 'WARN', 'SOFT', 'HARD']
    flaggedCount: int
    affectedInstitutions: int
    lastBacktest: str
    status: Literal['ACTIVE', 'DRAFT', 'RETIRED']

class PolicyStageChangeRequest(BaseModel):
    newStage: Literal['OBSERVE', 'WARN', 'SOFT', 'HARD']
    rationale: str
    officerName: str

class CapSimulationRequest(BaseModel):
    nriCapPercent: float = 15.0
    fnCapPercent: float = 5.0

# --- Identity Graph ---
class IdentityRecordModel(BaseModel):
    id: str
    personId: str
    name: str
    apaarId: Optional[str] = None
    ppid: Optional[str] = None
    institution: str
    trustLevel: int
    status: Literal['VERIFIED', 'CONFLICT', 'PROVISIONAL', 'CANDIDATE']
    mergedInto: Optional[str] = None
    matchScore: Optional[int] = None
    conflictType: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class MergeRequest(BaseModel):
    survivorId: str
    absorbedId: str
    rationale: str
    officerName: str

# --- Verifier Portal ---
class VerifierModel(BaseModel):
    id: str
    name: str
    type: str
    email: str
    status: Literal['ACTIVE', 'SUSPENDED', 'PENDING']
    verificationsToday: int = 0
    quotaDaily: int
    totalVerifications: int
    registeredOn: str
    lastActive: str
    purposesAllowed: List[str]

class VerifierStatusRequest(BaseModel):
    status: Literal['ACTIVE', 'SUSPENDED', 'PENDING']
    officerName: str

class VerifierQuotaRequest(BaseModel):
    quotaDaily: int

class VerifySimulationRequest(BaseModel):
    verifierId: str
    studentRef: str
    purpose: str
    consentRef: str

# --- Audit Event ---
class AuditEventModel(BaseModel):
    chainId: int
    seq: int
    ts: str
    actor: str
    actorType: Literal['system', 'officer', 'institution', 'student']
    action: str
    entity: str
    entityId: str
    payloadDigest: str
    prevHash: str
    thisHash: str
    valid: bool
    detail: str

class TamperSimulationRequest(BaseModel):
    seq: int
    tamperedActor: str = "[UNAUTHORIZED_TAMPER]"
    tamperedAction: str = "RECORD_ALTERED_DIRECTLY"

# --- Student Workflow Models ---
class DocumentUploadRequest(BaseModel):
    studentId: Optional[str] = "s1"
    type: str
    name: str
    issuer: Optional[str] = "Educational Board / Authority"
    rawContent: Optional[str] = None

class StudentClarificationRequest(BaseModel):
    studentId: Optional[str] = "s1"
    type: Literal['Clarification', 'Correction', 'Appeal', 'General']
    title: str
    detail: str

class StudentEnrolRequest(BaseModel):
    name: str
    apaarId: Optional[str] = None
    institutionId: str
    programme: str
    admissionDate: str
    poolCode: str = "REGULAR"
    gender: Optional[str] = "Unspecified"
    category: Optional[str] = "General"
    marksPercentile: Optional[float] = 85.0

class StudentMLCheckRequest(BaseModel):
    studentId: Optional[str] = "s1"
    age: Optional[float] = 18.5
    submissionDaysBeforeDeadline: Optional[float] = 5.0
    isMultiInstitutionClaim: Optional[bool] = False
    categoryCertVerified: Optional[bool] = True

# --- Institution Workflow Models ---
class InstitutionStudentCreateRequest(BaseModel):
    name: str
    apaarId: Optional[str] = None
    programme: str
    admissionDate: str
    poolCode: str = "REGULAR"
    gender: Optional[str] = "Unspecified"
    category: Optional[str] = "General"
    marksPercentile: Optional[float] = 85.0

class InstitutionBatchUploadRequest(BaseModel):
    batchId: Optional[str] = None
    filename: Optional[str] = "enrolment_batch.csv"
    records: Optional[List[Dict[str, Any]]] = None
    isDryRun: Optional[bool] = False

class InstitutionFindingResponseRequest(BaseModel):
    response: str
    officerOrAdminName: Optional[str] = "Dr. Priya Nair"

class InstitutionCaseResponseRequest(BaseModel):
    response: str
    evidenceSummary: Optional[str] = None
    adminName: Optional[str] = "Dr. Priya Nair"

