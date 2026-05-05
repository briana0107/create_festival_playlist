import { useMemo, useState } from "react";
import { BadgeCheck, ListChecks, Music2, Search, UploadCloud } from "lucide-react";

import { searchYouTube } from "./api/client.js";
import HomePage from "./pages/HomePage.jsx";
import LineupReviewPage from "./pages/LineupReviewPage.jsx";
import VideoReviewPage from "./pages/VideoReviewPage.jsx";
import PlaylistCreatePage from "./pages/PlaylistCreatePage.jsx";
import workflowImage from "./assets/festival-workflow.png";

const STEPS = [
  { id: "home", label: "Input", description: "라인업 입력", icon: UploadCloud },
  { id: "lineup", label: "Lineup", description: "아티스트 검수", icon: ListChecks },
  { id: "videos", label: "Videos", description: "영상 매칭", icon: Search },
  { id: "playlist", label: "Playlist", description: "재생목록 생성", icon: Music2 },
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

  const approvedLineupCount = lineupItems.filter((item) => item.approved).length;
  const approvedVideoCount = videoItems.filter((item) => item.approved).length;

  const stepAvailability = useMemo(
    () => ({
      home: true,
      lineup: lineupItems.length > 0,
      videos: approvedLineupCount > 0 || videoItems.length > 0,
      playlist: approvedVideoCount > 0,
    }),
    [approvedLineupCount, approvedVideoCount, lineupItems.length, videoItems.length],
  );

  const stats = [
    { label: "라인업", value: lineupItems.length },
    { label: "승인", value: approvedLineupCount },
    { label: "영상 후보", value: videoItems.length },
    { label: "플레이리스트", value: approvedVideoCount },
  ];

  async function handleSearchVideos(youtubeApiKey) {
    setBusy(true);
    setError("");
    try {
      const response = await searchYouTube({
        festivalName,
        items: lineupItems.filter((item) => item.approved),
        youtubeApiKey,
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
          <h1>페스티벌 라인업을 검수 가능한 플레이리스트로 정리합니다</h1>
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
            <span>{approvedLineupCount} ready</span>
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
