from fastapi import APIRouter, HTTPException
from app.db.state import state
from app.models import PolicyStageChangeRequest, CapSimulationRequest

router = APIRouter(prefix="/api/policy", tags=["Policy Studio"])

@router.get("/rules")
def get_policy_rules():
    return state.policy_engine.get_rules()

@router.post("/rules/{rule_id}/stage")
def change_rule_stage(rule_id: str, req: PolicyStageChangeRequest):
    try:
        res = state.policy_engine.update_stage(rule_id, req.newStage)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Log to cryptographic audit chain
    block = state.audit_engine.append_event(
        chain_id=3,
        actor=req.officerName,
        actor_type="officer",
        action="POLICY_STAGE_CHANGED",
        entity="policy_rule",
        entity_id=rule_id,
        detail=f"Officer {req.officerName} migrated rule {res['ruleName']} from {res['previousStage']} to {res['currentStage']}. Rationale: {req.rationale}",
        payload={"ruleId": rule_id, "prevStage": res["previousStage"], "newStage": res["currentStage"], "rationale": req.rationale}
    )

    return {
        "status": "SUCCESS",
        "result": res,
        "auditBlockSeq": block.seq,
        "message": f"Rule {rule_id} stage successfully updated to {req.newStage}."
    }

@router.post("/backtest")
def run_backtest():
    result = state.policy_engine.run_backtest()
    # Log backtest execution to audit chain
    state.audit_engine.append_event(
        chain_id=3,
        actor="Policy Engine",
        actor_type="system",
        action="HISTORICAL_BACKTEST_COMPLETED",
        entity="policy_studio",
        entity_id="AY-2026-27",
        detail="Historical back-testing completed against 18,400 records across 8 institutions. 39 flagged enrolments projected.",
        payload={"rulesEvaluated": result["rulesEvaluated"], "summary": result["summary"]}
    )
    return result

@router.post("/simulate-caps")
def simulate_caps(req: CapSimulationRequest):
    return state.policy_engine.simulate_caps(req.nriCapPercent, req.fnCapPercent)
