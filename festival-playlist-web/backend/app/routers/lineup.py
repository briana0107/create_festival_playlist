import logging

from fastapi import APIRouter, HTTPException, Request

from app.services.manual_input_service import parse_manual_text


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/from-text")
async def from_text(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    text = payload.get("text") if isinstance(payload, dict) else None
    date = payload.get("date") if isinstance(payload, dict) else None
    if not isinstance(text, str):
        raise HTTPException(status_code=400, detail="text is required")

    try:
        items = parse_manual_text(text, date)
        logger.info("Manual lineup parsed with %s lineup items", len(items))
        return {"items": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Manual lineup parsing failed")
        raise HTTPException(status_code=500, detail="Manual lineup parsing failed")
