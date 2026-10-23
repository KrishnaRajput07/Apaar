"""
Standalone FastAPI app that simulates the APAAR verification service.
Runs on port 8001 inside Docker Compose.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .apaar_mock import verify_apaar, generate_apaar_id, seed_known_apaar
import random

app = FastAPI(title="Mock APAAR Service", description="SIMULATION — not a real government API")

class VerifyRequest(BaseModel):
    apaar_id: str
    submitted_name: str = ""
    submitted_dob: str = ""

class SeedRequest(BaseModel):
    apaar_id: str
    name: str
    dob: str
    photo_hash: str = "demo_hash"

@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-apaar", "label": "SIMULATION"}

@app.post("/verify")
def verify(req: VerifyRequest):
    result = verify_apaar(req.apaar_id, req.submitted_name, req.submitted_dob)
    return {
        "apaar_id": result.apaar_id,
        "verified": result.verified,
        "name_match": result.name_match,
        "dob_match": result.dob_match,
        "photo_match": result.photo_match,
        "error": result.error,
        "label": "SIMULATION",
    }

@app.post("/seed")
def seed(req: SeedRequest):
    seed_known_apaar(req.apaar_id, req.name, req.dob, req.photo_hash)
    return {"status": "seeded", "apaar_id": req.apaar_id}

@app.post("/generate")
def generate():
    return {"apaar_id": generate_apaar_id(), "label": "SIMULATION"}
