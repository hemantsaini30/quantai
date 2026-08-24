// FILE LOCATION: quantai/apps/web/src/features/markets/components/StockSearch.jsx
import { useState } from "react";
import { search } from "../marketsService";

function StockSearch({ market }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleChange(e) {
    const value = e.target.value;
    setQuery(value);

    if (value.trim().length === 0) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const data = await search(value, market);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative w-full max-w-md">
      <input
        type="text"
        value={query}
        onChange={handleChange}
        placeholder="Search stocks by name or symbol..."
        className="w-full border border-slate/20 rounded-lg px-4 py-2 font-sans text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brass"
      />

      {query.trim().length > 0 && (
        <div className="absolute z-10 w-full bg-white border border-slate/20 rounded-lg mt-1 max-h-64 overflow-y-auto shadow-lg">
          {loading && <p className="p-3 text-sm text-slate font-sans">Searching...</p>}
          {!loading && results.length === 0 && (
            <p className="p-3 text-sm text-slate font-sans">No matches found</p>
          )}
          {!loading &&
            results.map((r) => (
              <div key={r.symbol} className="p-3 hover:bg-paper cursor-pointer border-b border-slate/5 last:border-0">
                <p className="font-sans text-sm text-ink">{r.name}</p>
                <p className="font-mono text-xs text-slate">
                  {r.symbol} · {r.sector}
                </p>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

export default StockSearch;