from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.db_models import UserRecord


SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = (
    settings.access_token_expire_minutes
)

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password
    )


def get_user_by_email(
    database: Session,
    email: str
) -> UserRecord | None:
    normalized_email = email.strip().lower()

    return (
        database.query(UserRecord)
        .filter(
            UserRecord.email == normalized_email
        )
        .first()
    )


def create_user(
    database: Session,
    email: str,
    full_name: str,
    password: str,
    role: str = "sales_rep"
) -> UserRecord:
    normalized_email = email.strip().lower()
    normalized_name = full_name.strip()
    normalized_role = role.strip().lower()

    if not normalized_email:
        raise ValueError("Email is required")

    if not normalized_name:
        raise ValueError("Full name is required")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters"
        )

    existing_user = get_user_by_email(
        database,
        normalized_email
    )

    if existing_user:
        raise ValueError(
            f"User already exists: {normalized_email}"
        )

    allowed_roles = {
        "admin",
        "manager",
        "sales_rep"
    }

    if normalized_role not in allowed_roles:
        raise ValueError(
            f"Invalid role: {normalized_role}"
        )

    user = UserRecord(
        email=normalized_email,
        full_name=normalized_name,
        hashed_password=hash_password(password),
        role=normalized_role,
        is_active=1
    )

    database.add(user)
    database.commit()
    database.refresh(user)

    return user


def authenticate_user(
    database: Session,
    email: str,
    password: str
) -> UserRecord | None:
    user = get_user_by_email(
        database,
        email
    )

    if user is None:
        return None

    if not bool(user.is_active):
        return None

    if not verify_password(
        password,
        user.hashed_password
    ):
        return None

    return user


def create_access_token(
    subject: str,
    role: str
) -> str:
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    issued_at = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "role": role,
        "iat": issued_at,
        "exp": expires_at,
        "iss": settings.app_name
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(
    token: str
) -> dict | None:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=settings.app_name
        )

    except jwt.PyJWTError:
        return None