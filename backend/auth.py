"""
auth.py — JWT Authentication utilities
"""
import os
import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

try:
    from passlib.context import CryptContext
    from jose import JWTError, jwt
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from database.db import get_db
from database.models import User

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("JWT_SECRET", "lead_intelligence_secret_key_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# pbkdf2_sha256 is compatible with all passlib/bcrypt versions
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto") if CRYPTO_AVAILABLE else None
bearer_scheme = HTTPBearer(auto_error=False)

# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("passlib not installed")
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    if not CRYPTO_AVAILABLE:
        return plain == hashed
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    if not CRYPTO_AVAILABLE:
        return str(data.get("sub", ""))
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        if not CRYPTO_AVAILABLE:
            return None
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

# ── Dependency ────────────────────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user
