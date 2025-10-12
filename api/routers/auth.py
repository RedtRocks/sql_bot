from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.jwt_handler import create_token
from models import get_user_by_username, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginRequest):
    user = get_user_by_username(body.username)
    if not user or not verify_password(body.username, body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(sub=user.username, role=user.role)
    return {"status": "ok", "token": token, "username": user.username, "role": user.role, "schema": user.schema}


