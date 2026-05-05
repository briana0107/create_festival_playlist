const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function loadManualText({ text }) {
  return requestJson("/api/lineup/from-text", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ text }),
  });
}

export async function searchYouTube({ festivalName, items, sessionId }) {
  const headers = jsonHeaders();
  if (sessionId) headers["X-Session-Id"] = sessionId;

  return requestJson("/api/youtube/search", {
    method: "POST",
    headers,
    body: JSON.stringify({
      festival_name: festivalName,
      items,
      session_id: sessionId,
    }),
  });
}

export async function getYouTubeAuthUrl() {
  return requestJson("/api/youtube/auth-url", {
    method: "GET",
  });
}

export async function getYouTubeStatus(sessionId) {
  const query = new URLSearchParams({ session_id: sessionId });
  return requestJson(`/api/youtube/status?${query.toString()}`, {
    method: "GET",
  });
}

export async function createPlaylist({ sessionId, playlistName, privacy, videos }) {
  return requestJson("/api/youtube/create-playlist", {
    method: "POST",
    headers: {
      ...jsonHeaders(),
      "X-Session-Id": sessionId,
    },
    body: JSON.stringify({
      session_id: sessionId,
      playlist_name: playlistName,
      privacy,
      videos,
    }),
  });
}

export async function getCreatePlaylistStatus(jobId) {
  const query = new URLSearchParams({ job_id: jobId });
  return requestJson(`/api/youtube/create-playlist-status?${query.toString()}`, {
    method: "GET",
  });
}

async function requestJson(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message = formatErrorDetail(data?.detail) || `Request failed with ${response.status}`;
    throw new Error(message);
  }

  return data;
}

function jsonHeaders() {
  return {
    "Content-Type": "application/json",
  };
}

function formatErrorDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) return item.msg;
        return "";
      })
      .filter(Boolean)
      .join(", ");
  }
  return "";
}
