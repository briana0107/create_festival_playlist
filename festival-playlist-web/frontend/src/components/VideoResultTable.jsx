import { ExternalLink, Trash2 } from "lucide-react";

export default function VideoResultTable({
  items,
  onChange,
  showArtist = true,
  showSearchQuery = true,
}) {
  const tableClassName = `data-table video-table ${
    !showArtist && !showSearchQuery ? "compact-video-table" : ""
  }`;

  function update(index, key, value) {
    const next = items.map((item, itemIndex) => {
      if (itemIndex !== index) return item;
      const updated = { ...item, [key]: value };
      if (key === "video_id") {
        updated.video_url = value ? `https://www.youtube.com/watch?v=${value}` : "";
      }
      return updated;
    });
    onChange(next);
  }

  function remove(index) {
    onChange(items.filter((_item, itemIndex) => itemIndex !== index));
  }

  if (!items.length) {
    return <div className="empty-state">아직 영상 후보가 없습니다.</div>;
  }

  return (
    <div className="table-wrap">
      <table className={tableClassName}>
        <thead>
          <tr>
            <th>미리보기</th>
            {showArtist ? <th>아티스트</th> : null}
            {showSearchQuery ? <th>검색어</th> : null}
            <th>Video ID</th>
            <th>제목</th>
            <th>채널</th>
            <th>URL</th>
            <th>선택 이유</th>
            <th>사용</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={`${item.artist_name}-${index}`}>
              <td>
                {item.video_id ? (
                  <img
                    className="video-thumb"
                    src={`https://i.ytimg.com/vi/${item.video_id}/mqdefault.jpg`}
                    alt=""
                    loading="lazy"
                  />
                ) : (
                  <span className="thumb-placeholder" />
                )}
              </td>
              {showArtist ? (
                <td>
                  <input
                    className="strong-input"
                    value={item.artist_name || ""}
                    onChange={(event) => update(index, "artist_name", event.target.value)}
                  />
                </td>
              ) : null}
              {showSearchQuery ? (
                <td>
                  <input value={item.search_query || ""} onChange={(event) => update(index, "search_query", event.target.value)} />
                </td>
              ) : null}
              <td>
                <input value={item.video_id || ""} onChange={(event) => update(index, "video_id", event.target.value)} />
              </td>
              <td>
                <input value={item.video_title || ""} onChange={(event) => update(index, "video_title", event.target.value)} />
              </td>
              <td>
                <input value={item.channel_title || ""} onChange={(event) => update(index, "channel_title", event.target.value)} />
              </td>
              <td>
                <div className="url-cell">
                  <input value={item.video_url || ""} onChange={(event) => update(index, "video_url", event.target.value)} />
                  {item.video_url ? (
                    <a href={item.video_url} target="_blank" rel="noreferrer">
                      <ExternalLink size={15} aria-hidden="true" />
                    </a>
                  ) : null}
                </div>
              </td>
              <td>
                <input value={item.reason || ""} onChange={(event) => update(index, "reason", event.target.value)} />
              </td>
              <td className="check-cell">
                <input
                  type="checkbox"
                  checked={Boolean(item.approved)}
                  onChange={(event) => update(index, "approved", event.target.checked)}
                  aria-label={`${item.artist_name || "영상"} 사용 여부`}
                />
              </td>
              <td>
                <button className="icon-button danger" type="button" onClick={() => remove(index)} title="행 삭제">
                  <Trash2 size={16} aria-hidden="true" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
