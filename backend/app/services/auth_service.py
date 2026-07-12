from datetime import datetime, timedelta, timezone
from os import getenv

import jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.db_models import UserRecord


SECRET_KEY = getenv(
    "QUOTEIQ_SECRET_KEY",
    "change-this-secret-before-deployment"
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

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
    return (
        database.query(UserRecord)
        .filter(UserRecord.email == email.lower())
        .first()
    )


def create_user(
    database: Session,
    email: str,
    full_name: str,
    password: str,
    role: str = "sales_rep"
) -> UserRecord:
    existing = get_user_by_email(
        database,
        email
    )

    if existing:
        raise ValueError(
            f"User already exists: {email}"
        )

    allowed_roles = {
        "admin",
        "manager",
        "sales_rep"
    }

    if role not in allowed_roles:
        raise ValueError(
            f"Invalid role: {role}"
        )

    user = UserRecord(
        email=email.lower(),
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
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

    payload = {
        "sub": subject,
        "role": role,
        "exp": expires_at
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
            algorithms=[ALGORITHM]
        )
    except jwt.PyJWTError:
        return None