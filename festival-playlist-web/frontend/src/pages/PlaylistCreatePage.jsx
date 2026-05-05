import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, CheckCircle2, ExternalLink, Link, Music2 } from "lucide-react";

import { createPlaylist, getYouTubeAuthUrl, getYouTubeStatus } from "../api/client.js";

export default function PlaylistCreatePage({
  festivalName,
  videos,
  youtubeSessionId,
  setYoutubeSessionId,
  onBack,
  onError,
}) {
  const [playlistName, setPlaylistName] = useState("");
  const [privacy, setPrivacy] = useState("private");
  const [authenticated, setAuthenticated] = useState(false);
  const [busyAuth, setBusyAuth] = useState(false);
  const [busyCreate, setBusyCreate] = useState(false);
  const [result, setResult] = useState(null);

  const approvedVideos = useMemo(
    () => videos.filter((video) => video.approved && video.video_id),
    [videos],
  );

  useEffect(() => {
    if (!playlistName) {
      setPlaylistName(`${festivalName || "Festival"} Playlist`);
    }
  }, [festivalName, playlistName]);

  useEffect(() => {
    if (!youtubeSessionId || authenticated) return undefined;

    let stopped = false;
    const timer = setInterval(async () => {
      try {
        const status = await getYouTubeStatus(youtubeSessionId);
        if (!stopped && status.authenticated) {
          setAuthenticated(true);
          clearInterval(timer);
        }
      } catch {
        clearInterval(timer);
      }
    }, 1500);

    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [youtubeSessionId, authenticated]);

  async function connectYouTube() {
    setBusyAuth(true);
    onError("");
    try {
      const response = await getYouTubeAuthUrl();
      setYoutubeSessionId(response.session_id);
      window.open(response.auth_url, "youtube-oauth", "width=520,height=720");
    } catch (err) {
      onError(err.message);
    } finally {
      setBusyAuth(false);
    }
  }

  async function submitCreatePlaylist() {
    if (!youtubeSessionId || !authenticated) {
      onError("YouTube OAuth connection is required");
      return;
    }

    setBusyCreate(true);
    setResult(null);
    onError("");
    try {
      const response = await createPlaylist({
        sessionId: youtubeSessionId,
        playlistName,
        privacy,
        videos: approvedVideos,
      });
      setResult(response);
    } catch (err) {
      onError(err.message);
    } finally {
      setBusyCreate(false);
    }
  }

  return (
    <section className="panel screen">
      <div className="section-header">
        <div>
          <p className="eyebrow">Playlist Create</p>
          <h2>YouTube 플레이리스트 생성</h2>
        </div>
        <span className="status-pill">{approvedVideos.length} videos</span>
      </div>

      <div className="form-grid">
        <label className="field field-wide">
          <span>playlist_name</span>
          <input value={playlistName} onChange={(event) => setPlaylistName(event.target.value)} />
        </label>
        <label className="field">
          <span>privacy</span>
          <select value={privacy} onChange={(event) => setPrivacy(event.target.value)}>
            <option value="private">private</option>
            <option value="unlisted">unlisted</option>
            <option value="public">public</option>
          </select>
        </label>
      </div>

      <div className="oauth-row">
        <button className="secondary-button" type="button" onClick={connectYouTube} disabled={busyAuth}>
          <Music2 size={18} aria-hidden="true" />
          <span>{busyAuth ? "Connecting" : "Connect YouTube"}</span>
        </button>
        <span className={`auth-state ${authenticated ? "ok" : ""}`}>
          {authenticated ? <CheckCircle2 size={16} aria-hidden="true" /> : <Link size={16} aria-hidden="true" />}
          <span>{authenticated ? "connected" : "not connected"}</span>
        </span>
      </div>

      <div className="playlist-preview">
        {approvedVideos.slice(0, 6).map((video) => (
          <span key={`${video.video_id}-${video.artist_name}`}>{video.artist_name}</span>
        ))}
        {approvedVideos.length > 6 ? <strong>+{approvedVideos.length - 6}</strong> : null}
      </div>

      <div className="action-row">
        <button className="secondary-button" type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Back</span>
        </button>
        <button
          className="primary-button"
          type="button"
          onClick={submitCreatePlaylist}
          disabled={busyCreate || approvedVideos.length === 0}
        >
          <Music2 size={18} aria-hidden="true" />
          <span>{busyCreate ? "Creating" : "Create Playlist"}</span>
        </button>
      </div>

      {result ? (
        <div className="result-box">
          <div>
            <p className="eyebrow">playlist_url</p>
            <a href={result.playlist_url} target="_blank" rel="noreferrer">
              {result.playlist_url}
              <ExternalLink size={16} aria-hidden="true" />
            </a>
          </div>
          <span>{result.added_count} added</span>
        </div>
      ) : null}
    </section>
  );
}
