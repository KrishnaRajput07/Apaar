"""Auth router — login, register (demo), me."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import hash_password, verify_password, create_access_token, get_current_user
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str  # student|institution|officer


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role, "name": user.full_name})
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.full_name, "role": user.role, "institution_id": user.institution_id},
    )


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    import uuid
    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role, "name": user.full_name})
    return TokenResponse(access_token=token, user={"id": user.id, "email": user.email, "name": user.full_name, "role": user.role})


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@router.post("/demo-login")
def demo_login(role: str, db: Session = Depends(get_db)):
    """Quick login by role for demo — no password needed."""
    role_email = {
        "student": "arjun@demo.edu",
        "institution": "admin@demo.edu",
        "officer": "officer@aicte.gov",
    }
    email = role_email.get(role)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Demo user not found. Run seeder first.")
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role, "name": user.full_name})
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.full_name, "role": user.role, "institution_id": user.institution_id},
    )
