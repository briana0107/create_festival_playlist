import logging
import os
import re

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.services.token_store import (
    consume_oauth_state,
    create_oauth_state,
    create_session_id,
    get_credentials,
    store_credentials,
)


logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
BAD_KEYWORDS = [
    "cover",
    "reaction",
    "lyrics",
    "lyric",
    "karaoke",
    "instrumental",
    "tutorial",
    "dance practice",
    "fanmade",
]
GOOD_KEYWORDS = ["official", "live", "festival", "mv", "music video", "performance"]


def build_auth_url():
    session_id = create_session_id()
    state = create_oauth_state(session_id)
    flow = _oauth_flow(state)
    auth_url, _state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return {"auth_url": auth_url, "session_id": session_id}


def handle_oauth_callback(authorization_response):
    state = _extract_state(authorization_response)
    session_id = consume_oauth_state(state)
    if not session_id:
        raise ValueError("Invalid or expired OAuth state")

    flow = _oauth_flow(state)
    flow.fetch_token(authorization_response=authorization_response)
    store_credentials(session_id, flow.credentials)
    logger.info("YouTube OAuth token stored in memory for temporary session")
    return session_id


def search_videos_for_lineup(lineup_items, festival_name, youtube_api_key, session_id):
    approved_items = [item for item in lineup_items if item.get("approved", True)]
    if not approved_items:
        raise ValueError("No approved artists to search")

    service = _youtube_search_service(youtube_api_key, session_id)
    results = []

    for item in approved_items:
        artist_name = str(item.get("artist_name") or "").strip()
        if not artist_name:
            continue

        query = _build_search_query(artist_name, festival_name)
        candidates = _search_candidates(service, query)
        selected = _select_candidate(artist_name, query, candidates)
        results.append(selected)

    return results


def create_playlist_with_videos(session_id, playlist_name, privacy, videos):
    service = _youtube_oauth_service(session_id)
    approved_videos = [video for video in videos if video.get("approved") and video.get("video_id")]

    if not approved_videos:
        raise ValueError("No approved videos to add")

    playlist_response = service.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": playlist_name,
                "description": "Created by Festival Playlist Web MVP.",
            },
            "status": {"privacyStatus": privacy},
        },
    ).execute()

    playlist_id = playlist_response["id"]
    added = []
    failed = []

    for video in approved_videos:
        video_id = video.get("video_id")
        try:
            service.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
            added.append(video_id)
        except Exception as exc:
            logger.warning("Failed to add video to playlist: %s", video_id)
            failed.append({"video_id": video_id, "reason": str(exc)})

    return {
        "playlist_id": playlist_id,
        "playlist_url": "https://www.youtube.com/playlist?list=%s" % playlist_id,
        "added_count": len(added),
        "failed_count": len(failed),
        "failed": failed,
    }


def _youtube_search_service(youtube_api_key, session_id):
    api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
    if api_key:
        return build("youtube", "v3", developerKey=api_key, cache_discovery=False)

    if session_id:
        return _youtube_oauth_service(session_id)

    raise ValueError("YouTube API key or OAuth session is required for search")


def _youtube_oauth_service(session_id):
    credentials = get_credentials(session_id)
    if not credentials:
        raise PermissionError("YouTube OAuth session is missing or expired")

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleAuthRequest())
        store_credentials(session_id, credentials)

    if not credentials.valid:
        raise PermissionError("YouTube OAuth session is invalid")

    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def _search_candidates(service, query):
    search_response = service.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=8,
        safeSearch="none",
        videoEmbeddable="true",
    ).execute()

    items = search_response.get("items", [])
    video_ids = [
        item.get("id", {}).get("videoId")
        for item in items
        if item.get("id", {}).get("videoId")
    ]
    durations = _video_durations(service, video_ids)

    candidates = []
    for item in items:
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        candidates.append(
            {
                "video_id": video_id,
                "video_title": snippet.get("title") or "",
                "channel_title": snippet.get("channelTitle") or "",
                "video_url": "https://www.youtube.com/watch?v=%s" % video_id,
                "duration_seconds": durations.get(video_id),
            }
        )
    return candidates


def _video_durations(service, video_ids):
    if not video_ids:
        return {}
    response = service.videos().list(
        part="contentDetails",
        id=",".join(video_ids),
    ).execute()

    durations = {}
    for item in response.get("items", []):
        video_id = item.get("id")
        duration = item.get("contentDetails", {}).get("duration")
        durations[video_id] = _parse_iso8601_duration(duration)
    return durations


def _select_candidate(artist_name, query, candidates):
    scored = []
    for candidate in candidates:
        reason_parts = []
        title = candidate["video_title"]
        channel = candidate["channel_title"]
        combined = "%s %s" % (title, channel)
        normalized = combined.lower()

        if _is_bad_candidate(normalized, candidate.get("duration_seconds")):
            continue

        score = 0
        for keyword in GOOD_KEYWORDS:
            if keyword in normalized:
                score += 2
                reason_parts.append(keyword)

        artist_tokens = _tokens(artist_name)
        if artist_tokens and all(token in normalized for token in artist_tokens[:3]):
            score += 4
            reason_parts.append("artist match")

        if "official" in channel.lower():
            score += 2
            reason_parts.append("official channel")

        scored.append((score, candidate, reason_parts))

    if scored:
        scored.sort(key=lambda value: value[0], reverse=True)
        score, candidate, reason_parts = scored[0]
        return {
            "artist_name": artist_name,
            "search_query": query,
            "video_id": candidate["video_id"],
            "video_title": candidate["video_title"],
            "channel_title": candidate["channel_title"],
            "video_url": candidate["video_url"],
            "reason": ", ".join(reason_parts) if reason_parts else "best available match",
            "approved": score >= 4,
        }

    fallback = candidates[0] if candidates else None
    if fallback:
        return {
            "artist_name": artist_name,
            "search_query": query,
            "video_id": fallback["video_id"],
            "video_title": fallback["video_title"],
            "channel_title": fallback["channel_title"],
            "video_url": fallback["video_url"],
            "reason": "fallback candidate; review manually",
            "approved": False,
        }

    return {
        "artist_name": artist_name,
        "search_query": query,
        "video_id": "",
        "video_title": "",
        "channel_title": "",
        "video_url": "",
        "reason": "no candidate found",
        "approved": False,
    }


def _build_search_query(artist_name, festival_name):
    parts = [artist_name, "official", "live", "festival"]
    if festival_name:
        parts.append(str(festival_name).strip())
    return " ".join([part for part in parts if part])


def _is_bad_candidate(normalized, duration_seconds):
    if "#shorts" in normalized or " shorts" in normalized:
        return True
    if duration_seconds is not None and duration_seconds <= 60:
        return True
    return any(keyword in normalized for keyword in BAD_KEYWORDS)


def _tokens(value):
    return [token for token in re.split(r"\s+", value.lower().strip()) if token]


def _parse_iso8601_duration(value):
    if not value:
        return None
    match = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", value)
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _oauth_flow(state):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/api/youtube/callback")

    if not client_id or not client_secret:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required")

    config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    flow = Flow.from_client_config(config, scopes=SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    return flow


def _extract_state(authorization_response):
    match = re.search(r"[?&]state=([^&]+)", authorization_response)
    if not match:
        raise ValueError("OAuth state is missing")
    return match.group(1)

