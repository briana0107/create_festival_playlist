import { ArrowLeft, ArrowRight, CheckCheck, CircleSlash2, Plus } from "lucide-react";

import LineupTable from "../components/LineupTable.jsx";

export default function LineupReviewPage({ items, setItems, onBack, onNext }) {
  const approvedCount = items.filter((item) => item.approved).length;

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
          <span className="status-pill">{approvedCount} approved</span>
          <button className="secondary-button compact" type="button" onClick={addArtist}>
            <Plus size={16} aria-hidden="true" />
            <span>Add</span>
          </button>
          <button className="secondary-button compact" type="button" onClick={() => setApproval(true)} disabled={!items.length}>
            <CheckCheck size={16} aria-hidden="true" />
            <span>All</span>
          </button>
          <button className="secondary-button compact" type="button" onClick={() => setApproval(false)} disabled={!items.length}>
            <CircleSlash2 size={16} aria-hidden="true" />
            <span>None</span>
          </button>
        </div>
      </div>

      <LineupTable items={items} onChange={setItems} />

      <div className="action-row">
        <button className="secondary-button" type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Back</span>
        </button>
        <button className="primary-button" type="button" onClick={onNext} disabled={approvedCount === 0}>
          <span>Search Videos</span>
          <ArrowRight size={18} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
