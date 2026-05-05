import logging
import html
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
SEARCH_PAGE_SIZE = 50
MAX_SEARCH_RESULTS_PER_ARTIST = 50


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


def search_videos_for_lineup(lineup_items, festival_name, session_id):
    approved_items = [item for item in lineup_items if item.get("approved", True)]
    if not approved_items:
        raise ValueError("No approved artists to search")

    service = _youtube_search_service(session_id)
    results = []

    for item in approved_items:
        artist_name = str(item.get("artist_name") or "").strip()
        if not artist_name:
            continue

        query = _build_search_query(artist_name, festival_name)
        candidates = _search_candidates(service, query)
        selected = _select_candidates(artist_name, query, candidates)
        results.extend(selected)

    return results


def create_playlist_with_videos(session_id, playlist_name, privacy, videos, progress_callback=None):
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
    playlist_url = "https://www.youtube.com/playlist?list=%s" % playlist_id
    added = []
    failed = []

    if progress_callback:
        progress_callback(
            {
                "playlist_id": playlist_id,
                "playlist_url": playlist_url,
                "processed_count": 0,
                "added_count": 0,
                "failed_count": 0,
            }
        )

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
        finally:
            if progress_callback:
                progress_callback(
                    {
                        "processed_count": len(added) + len(failed),
                        "added_count": len(added),
                        "failed_count": len(failed),
                        "failed": failed,
                    }
                )

    return {
        "playlist_id": playlist_id,
        "playlist_url": playlist_url,
        "added_count": len(added),
        "failed_count": len(failed),
        "failed": failed,
    }


def _youtube_search_service(session_id):
    api_key = os.getenv("YOUTUBE_API_KEY")
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
    items = []
    page_token = None

    while True:
        request = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": SEARCH_PAGE_SIZE,
            "safeSearch": "none",
            "videoEmbeddable": "true",
        }
        if page_token:
            request["pageToken"] = page_token

        search_response = service.search().list(**request).execute()
        remaining = MAX_SEARCH_RESULTS_PER_ARTIST - len(items)
        items.extend(search_response.get("items", [])[:remaining])
        if len(items) >= MAX_SEARCH_RESULTS_PER_ARTIST:
            break

        page_token = search_response.get("nextPageToken")
        if not page_token:
            break

    video_ids = [
        item.get("id", {}).get("videoId")
        for item in items
        if item.get("id", {}).get("videoId")
    ]
    video_details = _video_details(service, video_ids)

    candidates = []
    for item in items:
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        details = video_details.get(video_id, {})
        if not video_id:
            continue
        candidates.append(
            {
                "video_id": video_id,
                "video_title": _clean_text(details.get("video_title") or snippet.get("title") or ""),
                "channel_title": _clean_text(details.get("channel_title") or snippet.get("channelTitle") or ""),
                "published_at": details.get("published_at") or snippet.get("publishedAt") or "",
                "view_count": details.get("view_count"),
                "video_url": "https://www.youtube.com/watch?v=%s" % video_id,
                "duration_seconds": details.get("duration_seconds"),
            }
        )
    return _dedupe_candidates_by_title(candidates)


def _video_details(service, video_ids):
    if not video_ids:
        return {}

    details = {}
    for batch in _chunks(_unique(video_ids), 50):
        response = service.videos().list(
            part="contentDetails,snippet,statistics",
            id=",".join(batch),
        ).execute()

        for item in response.get("items", []):
            video_id = item.get("id")
            duration = item.get("contentDetails", {}).get("duration")
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            details[video_id] = {
                "video_title": snippet.get("title") or "",
                "channel_title": snippet.get("channelTitle") or "",
                "published_at": snippet.get("publishedAt") or "",
                "view_count": _parse_int(statistics.get("viewCount")),
                "duration_seconds": _parse_iso8601_duration(duration),
            }
    return details


def _select_candidates(artist_name, query, candidates):
    scored = []
    seen_video_ids = set()
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

        video_id = candidate.get("video_id")
        if video_id and video_id not in seen_video_ids:
            seen_video_ids.add(video_id)
            scored.append((score, candidate, reason_parts))

    if scored:
        scored.sort(key=lambda value: (value[0], _view_count_value(value[1])), reverse=True)
        return [
            {
                "artist_name": artist_name,
                "search_query": query,
                "video_id": candidate["video_id"],
                "video_title": candidate["video_title"],
                "channel_title": candidate["channel_title"],
                "published_at": candidate.get("published_at") or "",
                "view_count": candidate.get("view_count"),
                "video_url": candidate["video_url"],
                "reason": ", ".join(reason_parts) if reason_parts else "search candidate",
                "approved": score >= 4,
            }
            for score, candidate, reason_parts in scored
        ]

    fallback = candidates[0] if candidates else None
    if fallback:
        return [
            {
                "artist_name": artist_name,
                "search_query": query,
                "video_id": fallback["video_id"],
                "video_title": fallback["video_title"],
                "channel_title": fallback["channel_title"],
                "published_at": fallback.get("published_at") or "",
                "view_count": fallback.get("view_count"),
                "video_url": fallback["video_url"],
                "reason": "fallback candidate; review manually",
                "approved": False,
            }
        ]

    return [
        {
            "artist_name": artist_name,
            "search_query": query,
            "video_id": "",
            "video_title": "",
            "channel_title": "",
            "published_at": "",
            "view_count": None,
            "video_url": "",
            "reason": "no candidate found",
            "approved": False,
        }
    ]


def _build_search_query(artist_name, _festival_name):
    return "%s official music video" % artist_name


def _is_bad_candidate(normalized, duration_seconds):
    if "#shorts" in normalized or " shorts" in normalized:
        return True
    if duration_seconds is not None and duration_seconds <= 60:
        return True
    return any(keyword in normalized for keyword in BAD_KEYWORDS)


def _tokens(value):
    return [token for token in re.split(r"\s+", value.lower().strip()) if token]


def _dedupe_candidates_by_title(candidates):
    best_by_title = {}
    untitled = []

    for candidate in candidates:
        title_key = _normalize_title(candidate.get("video_title"))
        if not title_key:
            untitled.append(candidate)
            continue

        current = best_by_title.get(title_key)
        if current is None or _view_count_value(candidate) > _view_count_value(current):
            best_by_title[title_key] = candidate

    return list(best_by_title.values()) + untitled


def _normalize_title(value):
    text = _clean_text(value).lower()
    return re.sub(r"\s+", " ", text).strip()


def _clean_text(value):
    return html.unescape(str(value or "")).strip()


def _view_count_value(candidate):
    view_count = candidate.get("view_count")
    return view_count if isinstance(view_count, int) else -1


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _unique(values):
    seen = set()
    unique_values = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def _chunks(values, size):
    for index in range(0, len(values), size):
        yield values[index : index + size]


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
