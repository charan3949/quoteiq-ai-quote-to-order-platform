import logging

from sqlalchemy.orm import Session

from app.services.auth_service import create_user, get_user_by_email

logger = logging.getLogger(__name__)


# Fixed, documented demo accounts. Passwords are intentionally simple
# and public (see README) because these are for recruiter/demo login
# only — never reuse this pattern for real user accounts.
DEMO_ACCOUNTS = [
    {
        "email": "admin@quoteiq.demo",
        "full_name": "Demo Administrator",
        "password": "QuoteIQDemo123!",
        "role": "admin",
    },
    {
        "email": "manager@quoteiq.demo",
        "full_name": "Demo Manager",
        "password": "QuoteIQDemo123!",
        "role": "manager",
    },
    {
        "email": "sales@quoteiq.demo",
        "full_name": "Demo Sales Rep",
        "password": "QuoteIQDemo123!",
        "role": "sales_rep",
    },
]


def seed_demo_users(database: Session) -> None:
    """
    Idempotent: safe to call on every startup. Only creates accounts
    that don't already exist; never modifies or resets existing users
    or their data. This is what makes the demo survive redeploys.
    """
    for account in DEMO_ACCOUNTS:
        existing = get_user_by_email(database, account["email"])

        if existing is not None:
            continue

        try:
            create_user(
                database=database,
                email=account["email"],
                full_name=account["full_name"],
                password=account["password"],
                role=account["role"],
            )
            logger.info(
                "Seeded demo account: %s (%s)",
                account["email"],
                account["role"],
            )
        except ValueError as error:
            logger.warning(
                "Demo account seed skipped for %s: %s",
                account["email"],
                error,
            )