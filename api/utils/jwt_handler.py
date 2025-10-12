import jwt
import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET = os.getenv("JWT_SECRET", "dev-secret")


def create_token(sub: str, role: str, expires_minutes: int = 1440) -> str:  # 1440 minutes = 24 hours
  payload = {
    "sub": sub,
    "role": role,
    "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
  }
  return jwt.encode(payload, SECRET, algorithm="HS256")


def verify_token(token: str) -> dict:
  return jwt.decode(token, SECRET, algorithms=["HS256"])  # will raise if invalid


auth_scheme = HTTPBearer(auto_error=True)


def jwt_required(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> dict:
  try:
    payload = verify_token(credentials.credentials)
    return payload
  except Exception as e:
    raise HTTPException(status_code=401, detail="Invalid or expired token")


def admin_required(payload: dict = Depends(jwt_required)) -> dict:
  if payload.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Admin access required")
  return payload


