import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.audit import AuditLogRecord


logger = logging.getLogger(__name__)


def create_audit_log(
    database: Session,
    *,
    actor_email: str,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    status: str = "SUCCESS",
    details: dict[str, Any] | str | None = None,
    request_id: str | None = None,
) -> AuditLogRecord:
    if isinstance(details, dict):
        details_value = json.dumps(details)
    else:
        details_value = details

    audit_record = AuditLogRecord(
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        details=details_value,
        request_id=request_id,
    )

    database.add(audit_record)
    database.commit()
    database.refresh(audit_record)

    return audit_record


def record_audit_event(
    *,
    actor_email: str,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    status: str = "SUCCESS",
    details: dict[str, Any] | str | None = None,
    request_id: str | None = None,
) -> None:
    database = SessionLocal()

    try:
        create_audit_log(
            database=database,
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            details=details,
            request_id=request_id,
        )

    except Exception:
        database.rollback()

        logger.exception(
            "Failed to create audit event: %s",
            action,
        )

    finally:
        database.close()


def list_audit_logs(
    database: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    action: str | None = None,
    entity_type: str | None = None,
    actor_email: str | None = None,
) -> list[AuditLogRecord]:
    query = database.query(AuditLogRecord)

    if action:
        query = query.filter(
            AuditLogRecord.action == action
        )

    if entity_type:
        query = query.filter(
            AuditLogRecord.entity_type == entity_type
        )

    if actor_email:
        query = query.filter(
            AuditLogRecord.actor_email == actor_email
        )

    return (
        query.order_by(
            AuditLogRecord.timestamp.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )