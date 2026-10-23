import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List, Tuple

class StudentRiskScorer:
    """
    ML-driven Risk Scorer and Anomaly Detection for AICTE Student Enrolments.
    Combines an IsolationForest unsupervised anomaly detection model with
    domain-specific regulatory constraint penalties to output an explainable
    composite risk score [0 - 100].
    """
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.08,
            random_state=42
        )
        self._fit_baseline_model()

    def _fit_baseline_model(self):
        # Baseline training data: 300 normal student enrolment patterns
        # Features: [age, submission_days_before_deadline, trust_level, has_apaar, is_multi_claim, pool_mismatch]
        np.random.seed(42)
        n_samples = 300
        normal_ages = np.random.normal(loc=18.5, scale=0.8, size=n_samples).clip(17, 22)
        normal_days = np.random.uniform(low=5, high=30, size=n_samples)
        normal_trust = np.random.choice([2, 3, 4], size=n_samples, p=[0.25, 0.50, 0.25])
        normal_apaar = np.ones(n_samples)
        normal_multi = np.zeros(n_samples)
        normal_pool = np.zeros(n_samples)

        X_normal = np.column_stack([
            normal_ages, normal_days, normal_trust,
            normal_apaar, normal_multi, normal_pool
        ])

        # A few anomalous outliers in training set
        outlier_ages = np.array([29.0, 15.0, 31.0, 14.5, 33.0])
        outlier_days = np.array([0.1, 0.05, 0.2, 0.1, 0.3])
        outlier_trust = np.array([0, 1, 0, 1, 0])
        outlier_apaar = np.array([0, 0, 0, 1, 0])
        outlier_multi = np.array([1, 1, 1, 0, 1])
        outlier_pool = np.array([1, 0, 1, 1, 1])

        X_outliers = np.column_stack([
            outlier_ages, outlier_days, outlier_trust,
            outlier_apaar, outlier_multi, outlier_pool
        ])

        X_train = np.vstack([X_normal, X_outliers])
        self.model.fit(X_train)

    def evaluate_student(
        self,
        age: float,
        submission_days_before_deadline: float,
        trust_level: int,
        has_apaar: bool,
        is_multi_institution_claim: bool,
        pool_mismatch: bool,
        category_cert_verified: bool = True
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Calculates an anomaly score using the ML model and aggregates explainable factors.
        Returns: (composite_risk_score: int [0-100], risk_factors: List[Dict])
        """
        features = np.array([[
            float(age),
            float(submission_days_before_deadline),
            float(trust_level),
            1.0 if has_apaar else 0.0,
            1.0 if is_multi_institution_claim else 0.0,
            1.0 if pool_mismatch else 0.0
        ]])

        # Isolation forest raw decision function (lower means more anomalous)
        raw_score = self.model.decision_function(features)[0]
        # Normalize into anomaly scale [0 - 100]
        # In scikit-learn, normal points are around +0.1 to +0.25; anomalies are negative down to -0.3
        ml_anomaly_score = float(np.clip((0.20 - raw_score) / 0.40 * 100, 0, 100))

        risk_factors = []
        rule_penalty = 0

        # Multi-institution conflict
        if is_multi_institution_claim:
            rule_penalty += 45
            risk_factors.append({
                "factor": "Simultaneous Multi-Institution Enrolment",
                "impact": "+45 pts",
                "severity": "CRITICAL",
                "detail": "Single-seat lock invariant breached. Student record concurrently active in another institution."
            })

        # Missing APAAR
        if not has_apaar:
            rule_penalty += 25
            risk_factors.append({
                "factor": "Provisional / Unlinked APAAR Registry",
                "impact": "+25 pts",
                "severity": "HIGH",
                "detail": "Enrolment lacks authenticated APAAR ID. Relying on provisional PPID with L0/L1 trust."
            })

        # Pool breach / mismatch
        if pool_mismatch:
            rule_penalty += 20
            risk_factors.append({
                "factor": "Quota Pool Inconsistency",
                "impact": "+20 pts",
                "severity": "MEDIUM",
                "detail": "Claimed admission category differs from verified demographic or seat ledger pool cap."
            })

        # Age anomaly
        if age < 16.5 or age > 26.0:
            penalty = 15 if age > 26 else 20
            rule_penalty += penalty
            risk_factors.append({
                "factor": f"Age Distribution Anomaly ({age:.1f} yrs)",
                "impact": f"+{penalty} pts",
                "severity": "MEDIUM",
                "detail": "Admitted age deviates significantly from cohort mean (18.5 ± 1.5 yrs)."
            })

        # Last minute burst upload
        if submission_days_before_deadline < 1.0:
            rule_penalty += 12
            risk_factors.append({
                "factor": "Deadline Rush Upload Burst",
                "impact": "+12 pts",
                "severity": "LOW",
                "detail": "Record uploaded <24h before submission freeze, matching rapid batch-fill patterns."
            })

        # Low trust penalty
        if trust_level <= 1:
            rule_penalty += 10
            risk_factors.append({
                "factor": "Unverified Trust Tier (L0–L1)",
                "impact": "+10 pts",
                "severity": "LOW",
                "detail": "Demographic proof unvalidated against state or central education registries."
            })

        # Blend ML anomaly score (40%) and domain rule penalty (60%)
        composite = int(np.clip((0.35 * ml_anomaly_score) + (0.65 * rule_penalty), 0, 100))

        if not risk_factors:
            risk_factors.append({
                "factor": "Verified Cohort Baseline",
                "impact": "0 pts",
                "severity": "INFO",
                "detail": "Enrolment attributes align with approved AICTE demographic and timeline norms."
            })

        return composite, risk_factors
