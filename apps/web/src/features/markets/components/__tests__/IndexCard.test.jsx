// FILE LOCATION: quantai/apps/web/src/features/markets/components/__tests__/IndexCard.test.jsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import IndexCard from "../IndexCard";

describe("IndexCard", () => {
  it("renders the index name and price", () => {
    render(
      <IndexCard
        index={{ name: "NIFTY 50", last_price: 24500.5, change: 120.3, percent_change: 0.49 }}
      />
    );

    expect(screen.getByText("NIFTY 50")).toBeInTheDocument();
    expect(screen.getByText("24,500.5")).toBeInTheDocument();
  });

  it("shows a dash when last_price is null (yfinance failure case)", () => {
    render(
      <IndexCard
        index={{ name: "NIFTY 50", last_price: null, change: null, percent_change: null }}
      />
    );

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("does not render a percent-change line when percent_change is null", () => {
    render(
      <IndexCard
        index={{ name: "NIFTY 50", last_price: 100, change: null, percent_change: null }}
      />
    );

    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });
});