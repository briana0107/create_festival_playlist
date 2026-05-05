import { FileSpreadsheet } from "lucide-react";

export default function CsvUploader({ file, onChange }) {
  return (
    <label className="file-field">
      <span className="file-icon">
        <FileSpreadsheet size={18} aria-hidden="true" />
      </span>
      <span>CSV file</span>
      <input
        type="file"
        accept=".csv,text/csv"
        onChange={(event) => onChange(event.target.files?.[0] || null)}
      />
      <strong>{file ? file.name : "No CSV selected"}</strong>
    </label>
  );
}
