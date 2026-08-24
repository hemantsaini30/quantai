// FILE LOCATION: quantai/apps/web/src/features/markets/components/__tests__/StockTable.test.jsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StockTable from "../StockTable";

describe("StockTable", () => {
  const stocks = [
    { symbol: "TCS.NS", name: "Tata Consultancy Services", last_price: 3800, percent_change: 2.1 },
    { symbol: "INFY.NS", name: "Infosys", last_price: 1500, percent_change: -1.3 },
  ];

  it("renders the title and every stock row", () => {
    render(<StockTable title="Top Gainers" stocks={stocks} />);

    expect(screen.getByText("Top Gainers")).toBeInTheDocument();
    expect(screen.getByText("Tata Consultancy Services")).toBeInTheDocument();
    expect(screen.getByText("Infosys")).toBeInTheDocument();
  });

  it("shows an empty state message when stocks is an empty array", () => {
    render(<StockTable title="Top Gainers" stocks={[]} />);

    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("shows volume instead of percent change when valueLabel is Volume", () => {
    render(
      <StockTable
        title="Most Active"
        stocks={[{ symbol: "AAPL", name: "Apple", last_price: 200, volume: 5000000 }]}
        valueLabel="Volume"
      />
    );

    expect(screen.getByText("5,000,000")).toBeInTheDocument();
  });
});