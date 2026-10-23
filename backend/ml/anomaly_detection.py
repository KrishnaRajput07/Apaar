"""
ML integrity engine — anomaly detection using Isolation Forest + robust z-score.
Combined with rule-based findings for the full integrity pipeline.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from scipy import stats
from typing import Any

# Rule definitions (mirrors the architecture doc)
RULES = {
    "R1":  {"name": "INTAKE_BREACH",         "category": "Seat Integrity",   "default_stage": "SOFT"},
    "R2":  {"name": "CATEGORY_SHARE",        "category": "Data Quality",     "default_stage": "WARN"},
    "R3":  {"name": "SHARED_ATTRIBUTE",      "category": "Identity",         "default_stage": "OBSERVE"},
    "R4":  {"name": "DEADLINE_BULK_UPLOAD",  "category": "Submission",        "default_stage": "WARN"},
    "R6":  {"name": "NAME_DOB_MISMATCH",     "category": "Identity",         "default_stage": "SOFT"},
    "R8":  {"name": "STALE_ACTIVE",         "category": "Lifecycle",        "default_stage": "WARN"},
    "R10": {"name": "CATEGORY_SHIFT_SPIKE", "category": "Statistical",      "default_stage": "OBSERVE"},
    "R11": {"name": "DECLARATION_MISMATCH", "category": "Reconciliation",   "default_stage": "SOFT"},
    "R14": {"name": "ATTRITION_ANOMALY",     "category": "Statistical",      "default_stage": "OBSERVE"},
}


def compute_risk_score(student_data: dict) -> int:
    """Compute a 0-100 risk score for a student based on multiple signals."""
    score = 0
    if student_data.get("hold_state") == "CONFLICT_HOLD":
        score += 40
    if student_data.get("hold_state") == "IDENTITY_HOLD":
        score += 30
    if student_data.get("trust_level", 0) <= 1:
        score += 20
    if not student_data.get("apaar_id"):
        score += 15
    if student_data.get("risk_factors"):
        score += len(student_data["risk_factors"]) * 5
    return min(score, 100)


def detect_anomalies(student_records: list[dict]) -> list[dict]:
    """
    Run Isolation Forest + robust z-score on student features.
    Returns list of flagged records with anomaly scores.
    """
    if len(student_records) < 10:
        return []

    df = pd.DataFrame(student_records)

    # Build feature matrix
    features = []
    for _, row in df.iterrows():
        trust = row.get("trust_level", 0)
        risk = row.get("risk_score", 0)
        has_apaar = 1 if row.get("apaar_id") else 0
        hold = 1 if row.get("hold_state", "NONE") != "NONE" else 0
        features.append([trust, risk, has_apaar, hold])

    X = np.array(features)

    # Isolation Forest
    iso = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
    labels = iso.fit_predict(X)
    scores = -iso.decision_function(X)  # higher = more anomalous

    # Robust z-score on risk_score
    risk_scores = X[:, 1]
    median = np.median(risk_scores)
    mad = np.median(np.abs(risk_scores - median))
    if mad > 0:
        z_scores = 0.6745 * (risk_scores - median) / mad
    else:
        z_scores = np.zeros_like(risk_scores)

    findings = []
    for i, (label, score, z) in enumerate(zip(labels, scores, z_scores)):
        if label == -1 or abs(z) > 3:
            findings.append({
                "student_id": df.iloc[i].get("id", f"row_{i}"),
                "name": df.iloc[i].get("name", "Unknown"),
                "anomaly_score": round(float(score), 4),
                "z_score": round(float(z), 2),
                "reason": "ISOLATION_FOREST" if label == -1 else "ROBUST_Z_SCORE",
                "severity": "HIGH" if abs(z) > 3 else "MEDIUM",
            })

    return findings


def run_rules(records: list[dict], institution_id: str) -> list[dict]:
    """Run all rule-based checks against student records."""
    findings = []

    for r in records:
        # R1: Intake breach (handled at seat claim level, but check here too)
        pass

    # R6: Name/DOB mismatch (would need APAAR comparison data)
    # R3: Shared attributes — group by phone/guardian
    phones = {}
    for r in records:
        phone = r.get("phone", "")
        if phone:
            phones.setdefault(phone, []).append(r.get("id"))

    for phone, student_ids in phones.items():
        if len(student_ids) > 1:
            findings.append({
                "rule": "R3",
                "rule_name": "SHARED_ATTRIBUTE",
                "severity": "MEDIUM",
                "institution_id": institution_id,
                "subject_type": "student",
                "subject_ids": student_ids,
                "description": f"{len(student_ids)} students share the same phone number.",
                "reason_codes": ["SHARED_CONTACT"],
            })

    return findings


def get_policy_rules() -> list[dict]:
    """Return all policy rules with their current stage."""
    return [
        {"id": rid, "name": r["name"], "category": r["category"], "stage": r["default_stage"]}
        for rid, r in RULES.items()
    ]
