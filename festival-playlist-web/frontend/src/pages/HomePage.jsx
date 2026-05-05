import { useState } from "react";
import { ListPlus, Sparkles } from "lucide-react";

import { loadManualText } from "../api/client.js";
import ManualArtistInput from "../components/ManualArtistInput.jsx";

export default function HomePage({ festivalName, setFestivalName, onLineupLoaded, onError }) {
  const [manualText, setManualText] = useState("");
  const [busy, setBusy] = useState(false);

  async function submitManual() {
    if (!manualText.trim()) return onError("아티스트 이름을 입력해 주세요.");
    await run(async () => {
      const response = await loadManualText({ text: manualText });
      onLineupLoaded(response.items);
    });
  }

  async function run(task) {
    setBusy(true);
    onError("");
    try {
      await task();
    } catch (err) {
      onError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel screen">
      <div className="section-header">
        <div>
          <p className="eyebrow">Source</p>
          <h2>라인업 직접 입력</h2>
        </div>
        <span className="status-pill">직접 입력</span>
      </div>

      <div className="form-grid compact-grid">
        <label className="field field-wide">
          <span>페스티벌 이름</span>
          <input
            value={festivalName}
            onChange={(event) => setFestivalName(event.target.value)}
            placeholder="Seoul Jazz Festival"
          />
        </label>
      </div>

      <div className="input-stack">
        <ManualArtistInput value={manualText} onChange={setManualText} />
        <button className="primary-button" type="button" onClick={submitManual} disabled={busy}>
          <ListPlus size={18} aria-hidden="true" />
          <span>{busy ? "만드는 중" : "라인업 만들기"}</span>
        </button>
      </div>
    </section>
  );
}
