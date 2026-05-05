export default function ManualArtistInput({ value, onChange }) {
  return (
    <label className="field field-wide">
      <span>아티스트 이름</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={12}
        placeholder={"Artist A\nArtist B\nArtist C"}
      />
    </label>
  );
}
