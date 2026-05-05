import { Trash2 } from "lucide-react";

const COLUMNS = [
  "날짜",
  "일차",
  "아티스트",
  "스테이지",
  "시작",
  "신뢰도",
  "사용",
  "",
];

export default function LineupTable({ items, onChange }) {
  function update(index, key, value) {
    onChange(items.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item)));
  }

  function remove(index) {
    onChange(items.filter((_item, itemIndex) => itemIndex !== index));
  }

  if (!items.length) {
    return <div className="empty-state">아직 라인업이 없습니다.</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {COLUMNS.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={`${item.artist_name}-${index}`}>
              <td>
                <input
                  value={item.date || ""}
                  onChange={(event) => update(index, "date", clean(event.target.value))}
                  placeholder="YYYY-MM-DD"
                />
              </td>
              <td>
                <input
                  value={item.day_label || ""}
                  onChange={(event) => update(index, "day_label", clean(event.target.value))}
                />
              </td>
              <td>
                <input
                  className="strong-input"
                  value={item.artist_name || ""}
                  onChange={(event) => update(index, "artist_name", event.target.value)}
                  placeholder="아티스트"
                />
              </td>
              <td>
                <input value={item.stage || ""} onChange={(event) => update(index, "stage", clean(event.target.value))} />
              </td>
              <td>
                <input
                  value={item.start_time || ""}
                  onChange={(event) => update(index, "start_time", clean(event.target.value))}
                  placeholder="HH:mm"
                />
              </td>
              <td>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={Number(item.confidence ?? 0)}
                  onChange={(event) => update(index, "confidence", Number(event.target.value))}
                />
              </td>
              <td className="check-cell">
                <input
                  type="checkbox"
                  checked={Boolean(item.approved)}
                  onChange={(event) => update(index, "approved", event.target.checked)}
                  aria-label={`${item.artist_name || "라인업"} 사용 여부`}
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

function clean(value) {
  const text = value.trim();
  return text ? text : null;
}
