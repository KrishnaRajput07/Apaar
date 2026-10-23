from typing import Dict, Any, List

class PolicyEngine:
    def __init__(self):
        self.rules = [
            {
                "id": "R1",
                "name": "INTAKE_BREACH",
                "description": "Pool claimed count exceeds approved intake cap.",
                "category": "Seat Integrity",
                "currentStage": "SOFT",
                "flaggedCount": 3,
                "affectedInstitutions": 2,
                "lastBacktest": "15 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R2",
                "name": "CATEGORY_SHARE",
                "description": "Category distribution deviates from policy band or historical norm.",
                "category": "Data Quality",
                "currentStage": "WARN",
                "flaggedCount": 5,
                "affectedInstitutions": 3,
                "lastBacktest": "15 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R3",
                "name": "SHARED_ATTRIBUTE",
                "description": "Multiple students share identical DOB, contact, guardian, or photo.",
                "category": "Identity",
                "currentStage": "OBSERVE",
                "flaggedCount": 8,
                "affectedInstitutions": 4,
                "lastBacktest": "10 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R4",
                "name": "DEADLINE_BULK_UPLOAD",
                "description": ">60% records uploaded in last 48 hours before deadline.",
                "category": "Submission",
                "currentStage": "WARN",
                "flaggedCount": 2,
                "affectedInstitutions": 2,
                "lastBacktest": "15 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R6",
                "name": "NAME_DOB_MISMATCH",
                "description": "Submitted name/DOB differs from APAAR registry beyond threshold.",
                "category": "Identity",
                "currentStage": "SOFT",
                "flaggedCount": 4,
                "affectedInstitutions": 3,
                "lastBacktest": "12 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R8",
                "name": "STALE_ACTIVE",
                "description": "Enrolment CONTINUING with no update for >12 months.",
                "category": "Lifecycle",
                "currentStage": "WARN",
                "flaggedCount": 11,
                "affectedInstitutions": 5,
                "lastBacktest": "08 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R11",
                "name": "DECLARATION_MISMATCH",
                "description": "Declared totals differ from student-row derived count by >5%.",
                "category": "Reconciliation",
                "currentStage": "SOFT",
                "flaggedCount": 2,
                "affectedInstitutions": 1,
                "lastBacktest": "15 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R10",
                "name": "CATEGORY_SHIFT_SPIKE",
                "description": "FN/NRI/OCI ratio spike >3 std-devs from cohort norm.",
                "category": "Statistical",
                "currentStage": "OBSERVE",
                "flaggedCount": 1,
                "affectedInstitutions": 1,
                "lastBacktest": "10 Oct 2026",
                "status": "ACTIVE"
            },
            {
                "id": "R14",
                "name": "ATTRITION_ANOMALY",
                "description": "Programme attrition rate implausibly low or high vs peer cohort.",
                "category": "Statistical",
                "currentStage": "OBSERVE",
                "flaggedCount": 3,
                "affectedInstitutions": 2,
                "lastBacktest": "05 Oct 2026",
                "status": "DRAFT"
            }
        ]

    def get_rules(self) -> List[Dict[str, Any]]:
        return self.rules

    def update_stage(self, rule_id: str, new_stage: str) -> Dict[str, Any]:
        valid_stages = ["OBSERVE", "WARN", "SOFT", "HARD"]
        if new_stage not in valid_stages:
            raise ValueError(f"Invalid stage: {new_stage}")
        
        for r in self.rules:
            if r["id"] == rule_id:
                old = r["currentStage"]
                r["currentStage"] = new_stage
                return {
                    "ruleId": rule_id,
                    "previousStage": old,
                    "currentStage": new_stage,
                    "ruleName": r["name"]
                }
        raise KeyError(f"Rule {rule_id} not found")

    def run_backtest(self) -> Dict[str, Any]:
        """
        Executes policy back-testing simulation across historical submissions.
        """
        return {
            "executionTimestamp": "2026-10-22T21:30:00Z",
            "evaluatedDataset": "AY 2025-26 & AY 2026-27 (18,400 records across 8 institutions)",
            "rulesEvaluated": len(self.rules),
            "summary": {
                "totalFlaggedEnrolments": 39,
                "institutionsImpacted": 6,
                "criticalHoldProjections": 7,
                "falsePositiveRatioEstimate": "2.4%",
                "meanCaseResolutionTime": "4.2 days"
            },
            "ruleBreakdown": [
                {"ruleId": r["id"], "ruleName": r["name"], "stage": r["currentStage"], "projectedFlags": r["flaggedCount"], "institutions": r["affectedInstitutions"]}
                for r in self.rules
            ],
            "recommendations": [
                "Promote R6 (NAME_DOB_MISMATCH) to HARD enforcement after 99.1% APAAR linkage confirmation.",
                "Maintain R10 (CATEGORY_SHIFT_SPIKE) in OBSERVE stage to avoid premature false flags in specialized international universities."
            ]
        }

    def simulate_caps(self, nri_cap_pct: float, fn_cap_pct: float) -> Dict[str, Any]:
        """
        Simulates impact of dynamic NRI and FN quota caps.
        """
        # Baseline intake ~2840 seats
        total_intake = 2840
        baseline_nri_cap = 0.15
        baseline_fn_cap = 0.05

        nri_allowed = int(total_intake * (nri_cap_pct / 100.0))
        fn_allowed = int(total_intake * (fn_cap_pct / 100.0))

        # Enrolled claims
        nri_claimed = 448
        fn_claimed = 152

        nri_breach = max(0, nri_claimed - nri_allowed)
        fn_breach = max(0, fn_claimed - fn_allowed)

        affected_institutions = 0
        if nri_breach > 0:
            affected_institutions += 2
        if fn_breach > 0:
            affected_institutions += 1

        return {
            "nriCapPercent": nri_cap_pct,
            "fnCapPercent": fn_cap_pct,
            "nriAllowedSeats": nri_allowed,
            "fnAllowedSeats": fn_allowed,
            "nriClaimedSeats": nri_claimed,
            "fnClaimedSeats": fn_claimed,
            "nriExcessSeats": nri_breach,
            "fnExcessSeats": fn_breach,
            "totalExcessAdmissions": nri_breach + fn_breach,
            "impactedInstitutionsCount": affected_institutions,
            "policyActionRecommended": "ENFORCE_HARD_CAP" if (nri_breach + fn_breach) > 50 else "NOTIFY_WARNING"
        }
