// FILE LOCATION: quantai/apps/web/src/features/markets/components/MarketToggle.jsx

function MarketToggle({ market, onChange }) {
  return (
    <div className="inline-flex rounded-full border border-slate/20 p-1 bg-white">
      {["IN", "US"].map((m) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className={`px-4 py-1.5 rounded-full text-sm font-sans transition-colors ${
            market === m ? "bg-ink text-paper" : "text-slate hover:text-ink"
          }`}
        >
          {m === "IN" ? "India" : "United States"}
        </button>
      ))}
    </div>
  );
}

export default MarketToggle;