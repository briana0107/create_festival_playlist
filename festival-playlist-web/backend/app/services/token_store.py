import os
import secrets
import time


TOKEN_TTL_SECONDS = int(os.getenv("YOUTUBE_TOKEN_TTL_SECONDS", "3600"))
STATE_TTL_SECONDS = int(os.getenv("YOUTUBE_STATE_TTL_SECONDS", "600"))

_tokens = {}
_states = {}


def create_session_id():
    cleanup_expired()
    return secrets.token_urlsafe(32)


def create_oauth_state(session_id):
    cleanup_expired()
    state = secrets.token_urlsafe(32)
    _states[state] = {
        "session_id": session_id,
        "expires_at": time.time() + STATE_TTL_SECONDS,
    }
    return state


def consume_oauth_state(state):
    cleanup_expired()
    data = _states.pop(state, None)
    if not data:
        return None
    if data["expires_at"] < time.time():
        return None
    return data["session_id"]


def store_credentials(session_id, credentials):
    cleanup_expired()
    expires_at = time.time() + TOKEN_TTL_SECONDS
    _tokens[session_id] = {
        "credentials": credentials,
        "expires_at": expires_at,
    }


def get_credentials(session_id):
    cleanup_expired()
    data = _tokens.get(session_id)
    if not data:
        return None
    if data["expires_at"] < time.time():
        _tokens.pop(session_id, None)
        return None
    return data["credentials"]


def is_authenticated(session_id):
    credentials = get_credentials(session_id)
    if not credentials:
        return False
    return bool(getattr(credentials, "valid", False) or getattr(credentials, "refresh_token", None))


def cleanup_expired():
    now = time.time()
    expired_tokens = [key for key, value in _tokens.items() if value["expires_at"] < now]
    for key in expired_tokens:
        _tokens.pop(key, None)

    expired_states = [key for key, value in _states.items() if value["expires_at"] < now]
    for key in expired_states:
        _states.pop(key, None)
