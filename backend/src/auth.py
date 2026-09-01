import os
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-jwt-key-prod-newsfoundry-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def verify_password(plain_password: str, hashed_password: str | bytes | memoryview) -> bool:
    if isinstance(hashed_password, memoryview):
        hashed_bytes = hashed_password.tobytes()
    elif isinstance(hashed_password, str):
        hashed_bytes = hashed_password.encode("utf-8")
    else:
        hashed_bytes = hashed_password

    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_bytes)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)