import logging

from fastapi import APIRouter, HTTPException, Request

from app.services.csv_service import parse_csv_bytes
from app.services.manual_input_service import parse_manual_text
from app.utils.file_utils import read_upload_file


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/from-csv")
async def from_csv(request: Request):
    form = await request.form()
    upload = form.get("file")

    if upload is None:
        raise HTTPException(status_code=400, detail="CSV file is required")

    try:
        csv_bytes, _mime_type = await read_upload_file(upload, max_bytes=5 * 1024 * 1024)
        items = parse_csv_bytes(csv_bytes)
        logger.info("CSV lineup parsed with %s lineup items", len(items))
        return {"items": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("CSV lineup parsing failed")
        raise HTTPException(status_code=500, detail="CSV lineup parsing failed")


@router.post("/from-text")
async def from_text(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    text = payload.get("text") if isinstance(payload, dict) else None
    if not isinstance(text, str):
        raise HTTPException(status_code=400, detail="text is required")

    try:
        items = parse_manual_text(text)
        logger.info("Manual lineup parsed with %s lineup items", len(items))
        return {"items": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Manual lineup parsing failed")
        raise HTTPException(status_code=500, detail="Manual lineup parsing failed")
