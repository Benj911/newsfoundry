import os
import logging
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt

logger = logging.getLogger("uvicorn.error")

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-jwt-key-prod-newsfoundry-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def verify_password(plain_password: str, hashed_password: str | bytes | memoryview) -> bool:
    try:
        if isinstance(hashed_password, memoryview):
            hashed_bytes = hashed_password.tobytes()
        elif isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode("utf-8")
        elif isinstance(hashed_password, bytes):
            hashed_bytes = hashed_password
        else:
            return False

        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_bytes)
    except Exception as exc:
        logger.error(f"Erreur de vérification bcrypt : {exc}")
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)