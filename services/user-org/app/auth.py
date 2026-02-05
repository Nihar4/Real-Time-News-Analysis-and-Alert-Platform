import jwt
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from uuid import UUID
from .config import settings

ph = PasswordHasher()

def hash_password(plain: str) -> str:
    return ph.hash(plain)

def verify_password(hash_value: str | None, plain: str) -> bool:
    if not hash_value:
        return False
    try:
        return ph.verify(hash_value, plain)
    except VerifyMismatchError:
        return False

def create_access_token(user_id: UUID, email: str) -> tuple[str, int]:
    hours = int(settings.access_token_expire_hours)
    expire = datetime.now(tz=timezone.utc) + timedelta(hours=hours)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, hours

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
