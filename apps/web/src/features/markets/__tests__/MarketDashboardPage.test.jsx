// FILE LOCATION: quantai/apps/web/src/features/markets/__tests__/MarketDashboardPage.test.jsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import MarketDashboardPage from "../MarketDashboardPage";
import * as marketsService from "../marketsService";

vi.mock("../marketsService");

const mockOverview = {
  indices: [{ symbol: "^NSEI", name: "NIFTY 50", last_price: 24500, change: 100, percent_change: 0.4 }],
  top_gainers: [{ symbol: "TCS.NS", name: "TCS", last_price: 3800, percent_change: 2.1 }],
  top_losers: [{ symbol: "INFY.NS", name: "Infosys", last_price: 1500, percent_change: -1.3 }],
  most_active: [{ symbol: "RELIANCE.NS", name: "Reliance", last_price: 2900, volume: 5000000 }],
  sector_performance: [{ sector: "IT", average_percent_change: 1.2 }],
};

describe("MarketDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state, then renders overview data once loaded", async () => {
    marketsService.getOverview.mockResolvedValue(mockOverview);

    render(<MarketDashboardPage />);

    expect(screen.getByText("Loading market data...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("NIFTY 50")).toBeInTheDocument();
    });

    expect(screen.getByText("Top Gainers")).toBeInTheDocument();
    expect(screen.getByText("Top Losers")).toBeInTheDocument();
    expect(screen.getByText("Most Active")).toBeInTheDocument();
    expect(screen.getByText("Sector Performance")).toBeInTheDocument();
  });

  it("shows an error message if the API call fails", async () => {
    marketsService.getOverview.mockRejectedValue(new Error("Market data service unavailable"));

    render(<MarketDashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Market data service unavailable")).toBeInTheDocument();
    });
  });

  it("re-fetches overview data with the new market when the toggle is clicked", async () => {
    const user = userEvent.setup();
    marketsService.getOverview.mockResolvedValue(mockOverview);

    render(<MarketDashboardPage />);

    await waitFor(() => {
      expect(marketsService.getOverview).toHaveBeenCalledWith("IN");
    });

    await user.click(screen.getByText("United States"));

    await waitFor(() => {
      expect(marketsService.getOverview).toHaveBeenCalledWith("US");
    });
  });
});