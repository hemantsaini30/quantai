// FILE LOCATION: quantai/apps/web/src/features/markets/components/StockTable.jsx

function StockTable({ title, stocks, valueLabel = "% Change" }) {
  return (
    <div className="bg-white border border-slate/20 rounded-lg p-5">
      <h3 className="font-serif text-lg text-ink mb-4">{title}</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate border-b border-slate/10">
            <th className="font-sans font-normal pb-2">Symbol</th>
            <th className="font-sans font-normal pb-2 text-right">Price</th>
            <th className="font-sans font-normal pb-2 text-right">{valueLabel}</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock) => {
            const isPositive = stock.percent_change >= 0;
            return (
              <tr key={stock.symbol} className="border-b border-slate/5 last:border-0">
                <td className="py-2">
                  <span className="font-sans text-ink">{stock.name || stock.symbol}</span>
                  <span className="block font-mono text-xs text-slate">{stock.symbol}</span>
                </td>
                <td className="py-2 text-right font-mono text-ink">
                  {stock.last_price != null ? stock.last_price.toFixed(2) : "—"}
                </td>
                <td className={`py-2 text-right font-mono ${isPositive ? "text-gain" : "text-risk"}`}>
                  {valueLabel === "Volume"
                    ? stock.volume?.toLocaleString()
                    : `${isPositive ? "+" : ""}${stock.percent_change?.toFixed(2)}%`}
                </td>
              </tr>
            );
          })}
          {stocks.length === 0 && (
            <tr>
              <td colSpan={3} className="py-4 text-center text-slate font-sans text-sm">
                No data available
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default StockTable;