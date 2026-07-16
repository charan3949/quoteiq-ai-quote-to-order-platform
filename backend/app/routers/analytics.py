from fastapi import APIRouter, Depends, Query

from app.routers.auth import require_roles
from app.services.analytics_service import (
    get_approval_bottlenecks,
    get_monthly_trend,
    get_rep_performance,
    get_summary,
    get_top_customers,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/summary")
def summary(
    current_user=Depends(
        require_roles("manager", "admin")
    ),
):
    return get_summary()


@router.get("/trend")
def trend(
    months: int = Query(default=6, ge=1, le=24),
    current_user=Depends(
        require_roles("manager", "admin")
    ),
):
    return {"months": get_monthly_trend(months=months)}


@router.get("/customers")
def top_customers(
    limit: int = Query(default=5, ge=1, le=50),
    current_user=Depends(
        require_roles("manager", "admin")
    ),
):
    return {"customers": get_top_customers(limit=limit)}


@router.get("/reps")
def rep_performance(
    current_user=Depends(
        require_roles("manager", "admin")
    ),
):
    return {"reps": get_rep_performance()}


@router.get("/bottlenecks")
def bottlenecks(
    limit: int = Query(default=10, ge=1, le=50),
    current_user=Depends(
        require_roles("manager", "admin")
    ),
):
    return get_approval_bottlenecks(limit=limit)
