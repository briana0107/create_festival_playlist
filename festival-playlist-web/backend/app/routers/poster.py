import logging

from fastapi import APIRouter, HTTPException, Request

from app.services.vision_service import extract_lineup_from_poster
from app.utils.file_utils import read_image_url, read_upload_file
from app.utils.security import extract_bearer_token


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/extract")
async def extract_poster(request: Request):
    auth_header = request.headers.get("Authorization")
    api_key = extract_bearer_token(auth_header)
    if not api_key:
        raise HTTPException(status_code=401, detail="OpenAI API key is required")

    form = await request.form()
    upload = form.get("file")
    image_url = form.get("image_url")
    festival_name = form.get("festival_name") or None

    if upload is None and not image_url:
        raise HTTPException(status_code=400, detail="Poster image file or image_url is required")

    try:
        if image_url:
            image_bytes, mime_type = await read_image_url(image_url, max_bytes=50 * 1024 * 1024)
        else:
            image_bytes, mime_type = await read_upload_file(upload, max_bytes=50 * 1024 * 1024)
        items = extract_lineup_from_poster(api_key, image_bytes, mime_type, festival_name)
        logger.info("Poster extraction completed with %s lineup items", len(items))
        return {"items": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Poster extraction failed")
        raise HTTPException(status_code=502, detail="Poster extraction failed")
