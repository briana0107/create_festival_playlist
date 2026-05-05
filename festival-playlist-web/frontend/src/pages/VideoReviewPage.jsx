import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, CheckCheck, CircleSlash2, Search } from "lucide-react";

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
  const approvedCount = items.filter((item) => item.approved).length;
  const usableCount = items.filter((item) => item.approved && item.video_id).length;
  const artistGroups = useMemo(() => groupVideosByArtist(items), [items]);
  const [activeArtist, setActiveArtist] = useState("");
  const [topByViewLimit, setTopByViewLimit] = useState("manual");
  const activeGroup =
    artistGroups.find((group) => group.artistName === activeArtist) || artistGroups[0] || null;

  useEffect(() => {
    if (!artistGroups.length) {
      setActiveArtist("");
      return;
    }
    if (!artistGroups.some((group) => group.artistName === activeArtist)) {
      setActiveArtist(artistGroups[0].artistName);
    }
  }, [activeArtist, artistGroups]);

  function setApproval(approved) {
    setItems(items.map((item) => ({ ...item, approved })));
    setTopByViewLimit("manual");
  }

  function applyTopByViewsPerArtist(value) {
    setTopByViewLimit(value);

    if (value === "manual") return;
    if (value === "all") {
      setItems(items.map((item) => ({ ...item, approved: Boolean(item.video_id) })));
      return;
    }

    const limit = Number(value);
    const approvedIndexes = new Set();

    groupVideosByArtist(items).forEach((group) => {
      group.items
        .filter((entry) => entry.item.video_id)
        .sort((left, right) => viewCountValue(right.item) - viewCountValue(left.item))
        .slice(0, limit)
        .forEach((entry) => approvedIndexes.add(entry.index));
    });

    setItems(
      items.map((item, index) => ({
        ...item,
        approved: approvedIndexes.has(index),
      })),
    );
  }

  function updateActiveGroup(nextGroupItems) {
    if (!activeGroup) return;

    const activeIndexes = new Set(activeGroup.items.map((entry) => entry.index));
    let nextItemIndex = 0;
    const nextItems = [];

    items.forEach((item, index) => {
      if (!activeIndexes.has(index)) {
        nextItems.push(item);
        return;
      }

      if (nextItemIndex < nextGroupItems.length) {
        nextItems.push(nextGroupItems[nextItemIndex]);
        nextItemIndex += 1;
      }
    });

    setItems(nextItems);
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
          <label className="toolbar-select">
            <span>가수별 조회수 상위</span>
            <select value={topByViewLimit} onChange={(event) => applyTopByViewsPerArtist(event.target.value)} disabled={!items.length}>
              <option value="manual">수동</option>
              <option value="all">전체</option>
              <option value="5">5개</option>
              <option value="10">10개</option>
              <option value="20">20개</option>
              <option value="30">30개</option>
              <option value="50">50개</option>
            </select>
          </label>
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
        <button
          className="primary-button"
          type="button"
          onClick={onSearch}
          disabled={busy}
        >
          <Search size={18} aria-hidden="true" />
          <span>{busy ? "검색 중" : "영상 검색"}</span>
        </button>
      </div>

      {artistGroups.length ? (
        <div className="tabs artist-tabs" role="tablist" aria-label="Artist video groups">
          {artistGroups.map((group) => (
            <button
              key={group.artistName}
              className={`tab artist-tab ${group.artistName === activeGroup?.artistName ? "active" : ""}`}
              type="button"
              onClick={() => setActiveArtist(group.artistName)}
              role="tab"
              aria-selected={group.artistName === activeGroup?.artistName}
            >
              <span className="artist-name">{group.artistName}</span>
              <span className="artist-count">
                {group.approvedCount}/{group.items.length}
              </span>
            </button>
          ))}
        </div>
      ) : null}

      {activeGroup ? (
        <div className="artist-panel">
          <div className="artist-panel-header">
            <div>
              <p className="eyebrow">Artist</p>
              <h3>{activeGroup.artistName}</h3>
            </div>
            <span className="status-pill">{activeGroup.items.length}개 후보</span>
          </div>
          <VideoResultTable
            items={activeGroup.items.map((entry) => entry.item)}
            onChange={updateActiveGroup}
            showArtist={false}
            showSearchQuery={false}
          />
        </div>
      ) : (
        <VideoResultTable items={[]} onChange={setItems} />
      )}

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

function groupVideosByArtist(items) {
  const groupsByArtist = new Map();

  items.forEach((item, index) => {
    const artistName = String(item.artist_name || "이름 없음").trim() || "이름 없음";
    if (!groupsByArtist.has(artistName)) {
      groupsByArtist.set(artistName, {
        artistName,
        items: [],
        approvedCount: 0,
      });
    }

    const group = groupsByArtist.get(artistName);
    group.items.push({ item, index });
    if (item.approved && item.video_id) {
      group.approvedCount += 1;
    }
  });

  return Array.from(groupsByArtist.values());
}

function viewCountValue(item) {
  const value = Number(item.view_count);
  return Number.isFinite(value) ? value : -1;
}
