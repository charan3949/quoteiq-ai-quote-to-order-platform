from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import CopilotRequest, CopilotResponse

from app.routers.auth import get_current_user, require_roles
from app.services.enterprise_service import get_customer_portfolio, list_orders, quote_intelligence
from app.services.copilot_service import ask_copilot

router = APIRouter(prefix="/enterprise", tags=["Enterprise Views"])

@router.get("/customers")
def customers(current_user=Depends(get_current_user)):
    return {"customers": get_customer_portfolio()}

@router.get("/orders")
def orders(current_user=Depends(require_roles("manager", "admin"))):
    return {"orders": list_orders()}

@router.get("/quotes/{quote_id}/intelligence")
def intelligence(quote_id: str, current_user=Depends(get_current_user)):
    result = quote_intelligence(quote_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return result


@router.post("/copilot", response_model=CopilotResponse)
def copilot(request: CopilotRequest, current_user=Depends(get_current_user)):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message is required")
    if len(message) > 4000:
        raise HTTPException(status_code=422, detail="Message is too long")
    try:
        return ask_copilot(
            message=message,
            quote_id=request.quote_id,
            history=[item.model_dump() for item in request.history],
            actor_email=current_user.email,
            actor_role=current_user.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
