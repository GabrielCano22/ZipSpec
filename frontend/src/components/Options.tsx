interface Props {
  strict: boolean;
  setStrict: (v: boolean) => void;
  fuzzyThreshold: number;
  setFuzzyThreshold: (v: number) => void;
}

export default function Options({ strict, setStrict, fuzzyThreshold, setFuzzyThreshold }: Props) {
  return (
    <div className="options">
      <label className="options__toggle">
        <input
          type="checkbox"
          checked={strict}
          onChange={(e) => setStrict(e.target.checked)}
        />
        <span className="options__switch" />
        <span>Modo estricto</span>
      </label>

      <label className="options__range">
        <span>Fuzzy: {Math.round(fuzzyThreshold * 100)}%</span>
        <input
          type="range"
          min={50}
          max={100}
          value={fuzzyThreshold * 100}
          onChange={(e) => setFuzzyThreshold(Number(e.target.value) / 100)}
        />
      </label>
    </div>
  );
}
