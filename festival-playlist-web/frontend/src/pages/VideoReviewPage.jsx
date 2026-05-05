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
  const usableCount = items.filter((item) => item.approved && item.video_id).length;

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
          <span className="status-pill">{approvedCount}개 승인</span>
          <span className="status-pill">{usableCount}개 생성 대상</span>
          <button className="secondary-button compact" type="button" onClick={() => setApproval(true)} disabled={!items.length}>
            <CheckCheck size={16} aria-hidden="true" />
            <span>전체 선택</span>
          </button>
          <button className="secondary-button compact" type="button" onClick={() => setApproval(false)} disabled={!items.length}>
            <CircleSlash2 size={16} aria-hidden="true" />
            <span>전체 해제</span>
          </button>
        </div>
      </div>

      <div className="search-row">
        <ApiKeyInput
          label="YouTube 검색 API 키"
          value={youtubeApiKey}
          onChange={setYoutubeApiKey}
          placeholder="백엔드에 YOUTUBE_API_KEY가 있으면 비워둘 수 있습니다"
        />
        <button
          className="primary-button"
          type="button"
          onClick={() => onSearch(youtubeApiKey.trim())}
          disabled={busy}
        >
          <Search size={18} aria-hidden="true" />
          <span>{busy ? "검색 중" : "영상 검색"}</span>
        </button>
      </div>

      <VideoResultTable items={items} onChange={setItems} />

      <div className="action-row">
        <button className="secondary-button" type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>이전</span>
        </button>
        <button className="primary-button" type="button" onClick={onNext} disabled={!canContinue}>
          <span>플레이리스트 생성으로 이동</span>
          <ArrowRight size={18} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
