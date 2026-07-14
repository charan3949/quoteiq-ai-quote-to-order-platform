from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import require_roles
from app.services.audit_service import list_audit_logs


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


@router.get("/audit")
def get_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    action: str | None = None,
    entity_type: str | None = None,
    actor_email: str | None = None,
    database: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "manager",
            "admin",
        )
    ),
):
    logs = list_audit_logs(
        database,
        skip=skip,
        limit=limit,
        action=action,
        entity_type=entity_type,
        actor_email=actor_email,
    )

    return {
        "count": len(logs),
        "requested_by": current_user.email,
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp,
                "actor_email": log.actor_email,
                "actor_role": log.actor_role,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "status": log.status,
                "details": log.details,
                "request_id": log.request_id,
            }
            for log in logs
        ],
    }