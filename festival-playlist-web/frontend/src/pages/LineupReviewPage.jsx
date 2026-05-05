import { ArrowLeft, ArrowRight, CheckCheck, CircleSlash2, Plus } from "lucide-react";

import LineupTable from "../components/LineupTable.jsx";

export default function LineupReviewPage({ items, setItems, onBack, onNext }) {
  const approvedCount = items.filter((item) => item.approved).length;
  const searchableCount = items.filter((item) => item.approved && item.artist_name?.trim()).length;
  const incompleteCount = items.filter((item) => !item.artist_name?.trim()).length;
  const lowConfidenceCount = items.filter((item) => Number(item.confidence ?? 1) < 0.7).length;

  function addArtist() {
    setItems([
      ...items,
      {
        date: null,
        day_label: null,
        artist_name: "",
        stage: null,
        start_time: null,
        source_text: "",
        confidence: 1,
        approved: true,
        source: "manual",
      },
    ]);
  }

  function setApproval(approved) {
    setItems(items.map((item) => ({ ...item, approved })));
  }

  return (
    <section className="panel screen">
      <div className="section-header">
        <div>
          <p className="eyebrow">Lineup Review</p>
          <h2>라인업 검수</h2>
        </div>
        <div className="toolbar">
          <span className="status-pill">{approvedCount}명 승인</span>
          <button className="secondary-button compact" type="button" onClick={addArtist}>
            <Plus size={16} aria-hidden="true" />
            <span>추가</span>
          </button>
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

      <div className="review-summary" aria-label="라인업 상태">
        <span><strong>{items.length}</strong> 전체</span>
        <span><strong>{searchableCount}</strong> 검색 대상</span>
        <span><strong>{incompleteCount}</strong> 이름 누락</span>
        <span><strong>{lowConfidenceCount}</strong> 낮은 신뢰도</span>
      </div>

      <LineupTable items={items} onChange={setItems} />

      <div className="action-row">
        <button className="secondary-button" type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>이전</span>
        </button>
        <button className="primary-button" type="button" onClick={onNext} disabled={searchableCount === 0}>
          <span>영상 검색으로 이동</span>
          <ArrowRight size={18} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
