import { Trash2 } from "lucide-react";

const COLUMNS = ["일자", "아티스트", "선택", ""];

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
      <table className="data-table lineup-table">
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
                  type="date"
                  value={item.date || ""}
                  onChange={(event) => update(index, "date", clean(event.target.value))}
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
