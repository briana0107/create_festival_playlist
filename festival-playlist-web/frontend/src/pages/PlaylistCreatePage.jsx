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
  const [playlistNameTouched, setPlaylistNameTouched] = useState(false);
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
    if (!playlistNameTouched) {
      setPlaylistName(`${festivalName || "Festival"} Playlist`);
    }
  }, [festivalName, playlistNameTouched]);

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
      onError("YouTube 연결이 필요합니다.");
      return;
    }

    if (!playlistName.trim()) {
      onError("플레이리스트 이름을 입력해 주세요.");
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
        <span className="status-pill">{approvedVideos.length}개 영상</span>
      </div>

      <div className="form-grid">
        <label className="field field-wide">
          <span>플레이리스트 이름</span>
          <input
            value={playlistName}
            onChange={(event) => {
              setPlaylistNameTouched(true);
              setPlaylistName(event.target.value);
            }}
          />
        </label>
        <label className="field">
          <span>공개 범위</span>
          <select value={privacy} onChange={(event) => setPrivacy(event.target.value)}>
            <option value="private">비공개</option>
            <option value="unlisted">일부 공개</option>
            <option value="public">공개</option>
          </select>
        </label>
      </div>

      <div className="oauth-row">
        <button className="secondary-button" type="button" onClick={connectYouTube} disabled={busyAuth}>
          <Music2 size={18} aria-hidden="true" />
          <span>{busyAuth ? "연결 중" : "YouTube 연결"}</span>
        </button>
        <span className={`auth-state ${authenticated ? "ok" : ""}`}>
          {authenticated ? <CheckCircle2 size={16} aria-hidden="true" /> : <Link size={16} aria-hidden="true" />}
          <span>{authenticated ? "연결됨" : "연결 전"}</span>
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
          <span>이전</span>
        </button>
        <button
          className="primary-button"
          type="button"
          onClick={submitCreatePlaylist}
          disabled={busyCreate || approvedVideos.length === 0 || !authenticated || !playlistName.trim()}
        >
          <Music2 size={18} aria-hidden="true" />
          <span>{busyCreate ? "생성 중" : "플레이리스트 생성"}</span>
        </button>
      </div>

      {result ? (
        <div className="result-box">
          <div>
            <p className="eyebrow">Playlist URL</p>
            <a href={result.playlist_url} target="_blank" rel="noreferrer">
              {result.playlist_url}
              <ExternalLink size={16} aria-hidden="true" />
            </a>
          </div>
          <span>{result.added_count}개 추가</span>
        </div>
      ) : null}
    </section>
  );
}
