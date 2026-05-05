import { ImageUp } from "lucide-react";

export default function PosterUploader({ file, onChange }) {
  return (
    <label className="file-field">
      <span className="file-icon">
        <ImageUp size={18} aria-hidden="true" />
      </span>
      <span>Poster image</span>
      <input
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        onChange={(event) => onChange(event.target.files?.[0] || null)}
      />
      <strong>{file ? file.name : "No poster selected"}</strong>
    </label>
  );
}
