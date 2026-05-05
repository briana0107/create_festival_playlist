import logging
import re
import threading
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from googleapiclient.errors import HttpError

from app.services.playlist_job_store import create_job, get_job, update_job
from app.services.youtube_service import (
    build_auth_url,
    create_playlist_with_videos,
    handle_oauth_callback,
    search_videos_for_lineup,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search")
async def search(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON object body is required")

    session_id = request.headers.get("X-Session-Id") or payload.get("session_id")
    lineup_items = payload.get("items")
    festival_name = payload.get("festival_name")

    if not isinstance(lineup_items, list):
        raise HTTPException(status_code=400, detail="items must be a list")

    try:
        videos = search_videos_for_lineup(lineup_items, festival_name, session_id)
        logger.info("YouTube search completed for %s lineup items", len(lineup_items))
        return {"items": videos}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except HttpError as exc:
        logger.exception("YouTube API search failed")
        raise HTTPException(status_code=_http_error_status(exc), detail=_google_api_error_detail(exc))
    except Exception as exc:
        logger.exception("YouTube search failed")
        raise HTTPException(
            status_code=502,
            detail="YouTube search failed: %s" % _safe_exception_detail(exc),
        )


@router.get("/auth-url")
async def auth_url():
    try:
        data = build_auth_url()
        return data
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("OAuth URL generation failed")
        raise HTTPException(status_code=500, detail="OAuth URL generation failed")


@router.get("/callback")
async def callback(request: Request):
    try:
        handle_oauth_callback(str(request.url))
        html = """
        <!doctype html>
        <html>
          <head><title>YouTube OAuth</title></head>
          <body style="font-family: system-ui, sans-serif; padding: 32px;">
            <h1>YouTube 연결 완료</h1>
            <p>이 창을 닫고 앱으로 돌아가세요.</p>
            <script>setTimeout(() => window.close(), 800);</script>
          </body>
        </html>
        """
        return HTMLResponse(content=html)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("OAuth callback failed")
        raise HTTPException(status_code=500, detail="OAuth callback failed")


@router.get("/status")
async def status(request: Request):
    from app.services.token_store import is_authenticated

    session_id = request.query_params.get("session_id")
    if not session_id:
        return {"authenticated": False}
    return {"authenticated": is_authenticated(session_id)}


@router.post("/create-playlist")
async def create_playlist(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON object body is required")

    session_id = request.headers.get("X-Session-Id") or payload.get("session_id")
    playlist_name = payload.get("playlist_name")
    privacy = payload.get("privacy", "private")
    videos = payload.get("videos")

    if not session_id:
        raise HTTPException(status_code=401, detail="YouTube OAuth session is required")
    if not playlist_name:
        raise HTTPException(status_code=400, detail="playlist_name is required")
    if privacy not in ["private", "unlisted", "public"]:
        raise HTTPException(status_code=400, detail="Invalid privacy value")
    if not isinstance(videos, list):
        raise HTTPException(status_code=400, detail="videos must be a list")

    approved_count = len([video for video in videos if video.get("approved") and video.get("video_id")])
    if approved_count == 0:
        raise HTTPException(status_code=400, detail="No approved videos to add")

    job = create_job(approved_count)
    thread = threading.Thread(
        target=_run_create_playlist_job,
        args=(job["job_id"], session_id, playlist_name, privacy, videos),
        daemon=True,
    )
    thread.start()
    return JSONResponse(status_code=202, content=job)


@router.get("/create-playlist-status")
async def create_playlist_status(request: Request):
    job_id = request.query_params.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Playlist creation job not found")
    return job


def _run_create_playlist_job(job_id, session_id, playlist_name, privacy, videos):
    update_job(job_id, status="running", started_at=time.time())

    def update_progress(progress):
        update_job(job_id, **progress)

    try:
        result = create_playlist_with_videos(
            session_id,
            playlist_name,
            privacy,
            videos,
            progress_callback=update_progress,
        )
        update_job(job_id, status="completed", completed_at=time.time(), **result)
        logger.info("Playlist created with %s added videos", result.get("added_count"))
    except Exception as exc:
        logger.exception("Playlist creation failed")
        update_job(
            job_id,
            status="failed",
            completed_at=time.time(),
            error=str(exc) or "Playlist creation failed",
        )


def _http_error_status(exc):
    status = getattr(getattr(exc, "resp", None), "status", None)
    if isinstance(status, int) and 400 <= status < 600:
        return status
    return 502


def _google_api_error_detail(exc):
    try:
        import json

        payload = json.loads(exc.content.decode("utf-8"))
    except Exception:
        return "YouTube API request failed"

    error = payload.get("error", {})
    message = error.get("message") or "YouTube API request failed"
    reason = ""
    errors = error.get("errors")
    if isinstance(errors, list) and errors:
        reason = errors[0].get("reason") or ""

    if reason:
        return "YouTube API error (%s): %s" % (reason, message)
    return "YouTube API error: %s" % message


def _safe_exception_detail(exc):
    message = "%s: %s" % (exc.__class__.__name__, str(exc) or "unknown error")
    message = re.sub(r"AIza[0-9A-Za-z_-]+", "AIza...", message)
    return " ".join(message.split())[:300]
