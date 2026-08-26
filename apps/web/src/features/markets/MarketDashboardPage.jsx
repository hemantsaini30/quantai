// FILE LOCATION: quantai/apps/web/src/features/markets/MarketDashboardPage.jsx
import { useEffect, useState } from "react";
import { getOverview } from "./marketsService";
import MarketToggle from "./components/MarketToggle";
import IndexCard from "./components/IndexCard";
import StockTable from "./components/StockTable";
import SectorPerformance from "./components/SectorPerformance";
import StockSearch from "./components/StockSearch";

function MarketDashboardPage() {
  const [market, setMarket] = useState("IN");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);

    getOverview(market)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [market]);

  return (
    <div className="min-h-screen bg-paper px-6 py-8 max-w-6xl mx-auto">
      <header className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-serif text-3xl text-ink">QuantAI</h1>
          <p className="text-slate font-sans text-sm">Market overview</p>
        </div>
        <MarketToggle market={market} onChange={setMarket} />
      </header>

      <div className="mb-8">
        <StockSearch market={market} />
      </div>

      {loading && <p className="text-slate font-sans">Loading market data...</p>}
      {error && <p className="text-risk font-mono text-sm">{error}</p>}

      {data && (
        <div className="space-y-8">
          <section>
            <h2 className="font-serif text-xl text-ink mb-3">Indices</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.indices.map((idx) => (
                <IndexCard key={idx.symbol} index={idx} />
              ))}
            </div>
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <StockTable title="Top Gainers" stocks={data.top_gainers} />
            <StockTable title="Top Losers" stocks={data.top_losers} />
            <StockTable title="Most Active" stocks={data.most_active} valueLabel="Volume" />
          </section>

          <section>
            <SectorPerformance sectors={data.sector_performance} />
          </section>
        </div>
      )}
    </div>
  );
}

export default MarketDashboardPage;