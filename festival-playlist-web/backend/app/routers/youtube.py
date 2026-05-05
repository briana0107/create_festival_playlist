import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

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
    except Exception:
        logger.exception("YouTube search failed")
        raise HTTPException(status_code=502, detail="YouTube search failed")


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

    try:
        result = create_playlist_with_videos(session_id, playlist_name, privacy, videos)
        logger.info("Playlist created with %s added videos", result.get("added_count"))
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception:
        logger.exception("Playlist creation failed")
        raise HTTPException(status_code=502, detail="Playlist creation failed")
