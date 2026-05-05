import { useState } from "react";
import { ArrowLeft, ArrowRight, CheckCheck, CircleSlash2, Search } from "lucide-react";

import ApiKeyInput from "../components/ApiKeyInput.jsx";
import VideoResultTable from "../components/VideoResultTable.jsx";

export default function VideoReviewPage({
  items,
  setItems,
  onBack,
  onNext,
  onSearch,
  busy,
  canContinue,
}) {
  const [youtubeApiKey, setYoutubeApiKey] = useState("");
  const approvedCount = items.filter((item) => item.approved).length;

  function setApproval(approved) {
    setItems(items.map((item) => ({ ...item, approved })));
  }

  return (
    <section className="panel screen">
      <div className="section-header">
        <div>
          <p className="eyebrow">Video Search Review</p>
          <h2>영상 검색 결과 검수</h2>
        </div>
        <div className="toolbar">
          <span className="status-pill">{approvedCount} approved</span>
          <button className="secondary-button compact" type="button" onClick={() => setApproval(true)} disabled={!items.length}>
            <CheckCheck size={16} aria-hidden="true" />
            <span>All</span>
          </button>
          <button className="secondary-button compact" type="button" onClick={() => setApproval(false)} disabled={!items.length}>
            <CircleSlash2 size={16} aria-hidden="true" />
            <span>None</span>
          </button>
          <button
            className="primary-button compact"
            type="button"
            onClick={() => onSearch(youtubeApiKey.trim())}
            disabled={busy}
          >
            <Search size={18} aria-hidden="true" />
            <span>{busy ? "Searching" : "Search"}</span>
          </button>
        </div>
      </div>

      <ApiKeyInput
        label="YouTube Search API Key"
        value={youtubeApiKey}
        onChange={setYoutubeApiKey}
        placeholder="Optional when YOUTUBE_API_KEY is set on backend"
      />

      <VideoResultTable items={items} onChange={setItems} />

      <div className="action-row">
        <button className="secondary-button" type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Back</span>
        </button>
        <button className="primary-button" type="button" onClick={onNext} disabled={!canContinue}>
          <span>Create Playlist</span>
          <ArrowRight size={18} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
