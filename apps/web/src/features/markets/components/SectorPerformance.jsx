// FILE LOCATION: quantai/apps/web/src/features/markets/components/SectorPerformance.jsx

function SectorPerformance({ sectors }) {
  const maxAbs = Math.max(...sectors.map((s) => Math.abs(s.average_percent_change)), 1);

  return (
    <div className="bg-white border border-slate/20 rounded-lg p-5">
      <h3 className="font-serif text-lg text-ink mb-4">Sector Performance</h3>
      <div className="space-y-3">
        {sectors.map((sector) => {
          const isPositive = sector.average_percent_change >= 0;
          const widthPercent = (Math.abs(sector.average_percent_change) / maxAbs) * 100;

          return (
            <div key={sector.sector} className="flex items-center gap-3">
              <span className="font-sans text-sm text-ink w-40 truncate">{sector.sector}</span>
              <div className="flex-1 h-2 bg-slate/10 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${isPositive ? "bg-gain" : "bg-risk"}`}
                  style={{ width: `${widthPercent}%` }}
                />
              </div>
              <span className={`font-mono text-sm w-16 text-right ${isPositive ? "text-gain" : "text-risk"}`}>
                {isPositive ? "+" : ""}
                {sector.average_percent_change.toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default SectorPerformance;