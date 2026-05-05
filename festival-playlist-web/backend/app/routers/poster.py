import logging
import os
import re

from fastapi import APIRouter, HTTPException, Request
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

from app.services.vision_service import extract_lineup_from_poster
from app.utils.file_utils import read_image_url, read_upload_file
from app.utils.security import extract_bearer_token


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/extract")
async def extract_poster(request: Request):
    auth_header = request.headers.get("Authorization")
    api_key = _openai_api_key(auth_header)
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
    except AuthenticationError:
        logger.exception("OpenAI authentication failed")
        raise HTTPException(
            status_code=401,
            detail="OpenAI authentication failed. Check OPENAI_API_KEY in Render.",
        )
    except PermissionDeniedError:
        logger.exception("OpenAI permission denied")
        raise HTTPException(
            status_code=403,
            detail="OpenAI permission denied. Check project access and model permissions.",
        )
    except RateLimitError:
        logger.exception("OpenAI rate limit or quota error")
        raise HTTPException(
            status_code=429,
            detail="OpenAI rate limit or quota error. Check billing, quota, or retry later.",
        )
    except (BadRequestError, NotFoundError) as exc:
        logger.exception("OpenAI request was rejected")
        raise HTTPException(
            status_code=400,
            detail="OpenAI request failed: %s" % _safe_error_message(exc),
        )
    except (APIConnectionError, APITimeoutError):
        logger.exception("OpenAI connection failed")
        raise HTTPException(
            status_code=502,
            detail="OpenAI connection failed. Retry after a moment.",
        )
    except OpenAIError as exc:
        logger.exception("OpenAI API failed")
        raise HTTPException(
            status_code=502,
            detail="OpenAI API failed: %s" % _safe_error_message(exc),
        )
    except Exception:
        logger.exception("Poster extraction failed")
        raise HTTPException(status_code=502, detail="Poster extraction failed")


def _openai_api_key(auth_header):
    return _normalize_api_key(extract_bearer_token(auth_header) or os.getenv("OPENAI_API_KEY"))


def _normalize_api_key(value):
    if not value:
        return None
    text = str(value).strip().strip('"').strip("'")
    if text.startswith("OPENAI_API_KEY="):
        text = text.split("=", 1)[1].strip().strip('"').strip("'")
    return text or None


def _safe_error_message(exc):
    message = getattr(exc, "message", None) or str(exc) or exc.__class__.__name__
    message = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-...", message)
    return " ".join(message.split())[:300]
