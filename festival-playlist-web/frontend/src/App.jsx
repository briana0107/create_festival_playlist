import { useMemo, useState } from "react";
import { BadgeCheck, ListChecks, Music2, Search, UploadCloud } from "lucide-react";

import { searchYouTube } from "./api/client.js";
import HomePage from "./pages/HomePage.jsx";
import LineupReviewPage from "./pages/LineupReviewPage.jsx";
import VideoReviewPage from "./pages/VideoReviewPage.jsx";
import PlaylistCreatePage from "./pages/PlaylistCreatePage.jsx";
import workflowImage from "./assets/festival-workflow.png";

const STEPS = [
  { id: "home", label: "입력", description: "직접 입력", icon: UploadCloud },
  { id: "lineup", label: "라인업", description: "아티스트 검수", icon: ListChecks },
  { id: "videos", label: "영상", description: "후보 검수", icon: Search },
  { id: "playlist", label: "생성", description: "YouTube 저장", icon: Music2 },
];

export default function App() {
  const [step, setStep] = useState("home");
  const [festivalName, setFestivalName] = useState("");
  const [lineupItems, setLineupItems] = useState([]);
  const [videoItems, setVideoItems] = useState([]);
  const [youtubeSessionId, setYoutubeSessionId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const currentStepIndex = useMemo(
    () => STEPS.findIndex((item) => item.id === step),
    [step],
  );

  const searchableLineupCount = lineupItems.filter(
    (item) => item.approved && item.artist_name?.trim(),
  ).length;
  const approvedVideoCount = videoItems.filter((item) => item.approved).length;

  const stepAvailability = useMemo(
    () => ({
      home: true,
      lineup: lineupItems.length > 0,
      videos: searchableLineupCount > 0 || videoItems.length > 0,
      playlist: approvedVideoCount > 0,
    }),
    [approvedVideoCount, lineupItems.length, searchableLineupCount, videoItems.length],
  );

  const stats = [
    { label: "라인업", value: lineupItems.length },
    { label: "검색 대상", value: searchableLineupCount },
    { label: "영상 후보", value: videoItems.length },
    { label: "생성 대상", value: approvedVideoCount },
  ];
  const displayFestivalName = festivalName.trim() || "페스티벌 이름 미입력";

  async function handleSearchVideos() {
    setBusy(true);
    setError("");
    try {
      const response = await searchYouTube({
        festivalName,
        items: lineupItems.filter((item) => item.approved && item.artist_name?.trim()),
        sessionId: youtubeSessionId,
      });
      setVideoItems(response.items);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function handleLineupLoaded(items) {
    setLineupItems(items);
    setVideoItems([]);
    setStep("lineup");
  }

  function canOpenStep(stepId, index) {
    return index <= currentStepIndex || stepAvailability[stepId];
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <div className="brand-mark">
            <Music2 size={18} aria-hidden="true" />
            <span>Festival Playlist Studio</span>
          </div>
          <div>
            <p className="eyebrow">Festival</p>
            <h1>{displayFestivalName}</h1>
          </div>
          <div className="metrics" aria-label="Workflow summary">
            {stats.map((item) => (
              <span key={item.label}>
                <strong>{item.value}</strong>
                {item.label}
              </span>
            ))}
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <img src={workflowImage} alt="" />
          <div className="visual-badge">
            <BadgeCheck size={16} />
            <span>{searchableLineupCount}명 준비</span>
          </div>
        </div>
      </header>

      <nav className="stepper" aria-label="Workflow">
        {STEPS.map((item, index) => {
          const Icon = item.icon;
          const state = index === currentStepIndex ? "active" : index < currentStepIndex ? "done" : "";
          const enabled = canOpenStep(item.id, index);
          return (
            <button
              key={item.id}
              className={`step ${state}`}
              type="button"
              onClick={() => {
                if (enabled) setStep(item.id);
              }}
              disabled={!enabled}
            >
              <span className="step-icon">
                <Icon size={16} aria-hidden="true" />
              </span>
              <span>
                <strong>{item.label}</strong>
                <small>{item.description}</small>
              </span>
            </button>
          );
        })}
      </nav>

      <main className="workspace">
        {error ? <div className="error-banner">{error}</div> : null}

        {step === "home" ? (
          <HomePage
            festivalName={festivalName}
            setFestivalName={setFestivalName}
            onLineupLoaded={handleLineupLoaded}
            onError={setError}
          />
        ) : null}

        {step === "lineup" ? (
          <LineupReviewPage
            items={lineupItems}
            setItems={setLineupItems}
            onBack={() => setStep("home")}
            onNext={() => setStep("videos")}
          />
        ) : null}

        {step === "videos" ? (
          <VideoReviewPage
            items={videoItems}
            setItems={setVideoItems}
            onBack={() => setStep("lineup")}
            onNext={() => setStep("playlist")}
            onSearch={handleSearchVideos}
            busy={busy}
            canContinue={approvedVideoCount > 0}
          />
        ) : null}

        {step === "playlist" ? (
          <PlaylistCreatePage
            festivalName={festivalName}
            videos={videoItems}
            youtubeSessionId={youtubeSessionId}
            setYoutubeSessionId={setYoutubeSessionId}
            onBack={() => setStep("videos")}
            onError={setError}
          />
        ) : null}
      </main>
    </div>
  );
}
