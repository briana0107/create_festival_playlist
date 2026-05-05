export default function ManualArtistInput({ value, onChange }) {
  return (
    <label className="field field-wide">
      <span>Artist names</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={12}
        placeholder={"Artist A\nArtist B\nArtist C"}
      />
    </label>
  );
}
