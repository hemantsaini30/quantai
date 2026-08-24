// FILE LOCATION: quantai/apps/web/src/features/markets/components/IndexCard.jsx

function IndexCard({ index }) {
  const isPositive = index.percent_change >= 0;

  return (
    <div className="bg-white border border-slate/20 rounded-lg p-5">
      <p className="font-sans text-sm text-slate mb-2">{index.name}</p>
      <p className="font-mono text-2xl text-ink mb-1">
        {index.last_price != null
          ? index.last_price.toLocaleString(undefined, { maximumFractionDigits: 2 })
          : "—"}
      </p>
      {index.percent_change != null && (
        <p className={`font-mono text-sm ${isPositive ? "text-gain" : "text-risk"}`}>
          {isPositive ? "+" : ""}
          {index.change?.toFixed(2)} ({isPositive ? "+" : ""}
          {index.percent_change.toFixed(2)}%)
        </p>
      )}
    </div>
  );
}

export default IndexCard;