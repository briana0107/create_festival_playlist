import { useState } from "react";
import { FileSpreadsheet, ImageUp, ListPlus, Sparkles } from "lucide-react";

import { extractPoster, loadCsv, loadManualText } from "../api/client.js";
import ApiKeyInput from "../components/ApiKeyInput.jsx";
import PosterUploader from "../components/PosterUploader.jsx";
import CsvUploader from "../components/CsvUploader.jsx";
import ManualArtistInput from "../components/ManualArtistInput.jsx";

const TABS = [
  { id: "poster", label: "Poster Upload", icon: ImageUp },
  { id: "csv", label: "CSV Upload", icon: FileSpreadsheet },
  { id: "manual", label: "Manual Input", icon: ListPlus },
];

export default function HomePage({ festivalName, setFestivalName, onLineupLoaded, onError }) {
  const [activeTab, setActiveTab] = useState("poster");
  const [openAiApiKey, setOpenAiApiKey] = useState("");
  const [posterFile, setPosterFile] = useState(null);
  const [posterImageUrl, setPosterImageUrl] = useState("");
  const [csvFile, setCsvFile] = useState(null);
  const [manualText, setManualText] = useState("");
  const [busy, setBusy] = useState(false);

  async function submitPoster() {
    if (!openAiApiKey.trim()) return onError("OpenAI API key is required");
    if (!posterFile && !posterImageUrl.trim()) return onError("Poster image file or image URL is required");

    await run(async () => {
      const response = await extractPoster({
        festivalName,
        openAiApiKey: openAiApiKey.trim(),
        file: posterFile,
        imageUrl: posterImageUrl.trim(),
      });
      onLineupLoaded(response.items);
    });
  }

  async function submitCsv() {
    if (!csvFile) return onError("CSV file is required");
    await run(async () => {
      const response = await loadCsv({ file: csvFile });
      onLineupLoaded(response.items);
    });
  }

  async function submitManual() {
    if (!manualText.trim()) return onError("Manual input is empty");
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
          <h2>라인업 가져오기</h2>
        </div>
        <span className="status-pill">{TABS.find((tab) => tab.id === activeTab)?.label}</span>
      </div>

      <div className="form-grid compact-grid">
        <label className="field field-wide">
          <span>Festival name</span>
          <input
            value={festivalName}
            onChange={(event) => setFestivalName(event.target.value)}
            placeholder="Seoul Jazz Festival"
          />
        </label>
      </div>

      <div className="tabs source-tabs" role="tablist" aria-label="Input type">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? "active" : ""}`}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              role="tab"
              aria-selected={activeTab === tab.id}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {activeTab === "poster" ? (
        <div className="input-stack">
          <ApiKeyInput
            label="OpenAI API Key"
            value={openAiApiKey}
            onChange={setOpenAiApiKey}
          />
          <label className="field field-wide">
            <span>poster_image_url</span>
            <input
              value={posterImageUrl}
              onChange={(event) => setPosterImageUrl(event.target.value)}
              placeholder="https://example.com/festival-poster.jpg"
            />
          </label>
          <PosterUploader file={posterFile} onChange={setPosterFile} />
          <button className="primary-button" type="button" onClick={submitPoster} disabled={busy}>
            <ImageUp size={18} aria-hidden="true" />
            <span>{busy ? "Extracting" : "Extract Lineup"}</span>
          </button>
        </div>
      ) : null}

      {activeTab === "csv" ? (
        <div className="input-stack">
          <CsvUploader file={csvFile} onChange={setCsvFile} />
          <button className="primary-button" type="button" onClick={submitCsv} disabled={busy}>
            <FileSpreadsheet size={18} aria-hidden="true" />
            <span>{busy ? "Loading" : "Load CSV"}</span>
          </button>
        </div>
      ) : null}

      {activeTab === "manual" ? (
        <div className="input-stack">
          <ManualArtistInput value={manualText} onChange={setManualText} />
          <button className="primary-button" type="button" onClick={submitManual} disabled={busy}>
            <Sparkles size={18} aria-hidden="true" />
            <span>{busy ? "Loading" : "Create Lineup"}</span>
          </button>
        </div>
      ) : null}
    </section>
  );
}
