// FILE LOCATION: quantai/apps/web/src/features/markets/components/__tests__/StockSearch.test.jsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import StockSearch from "../StockSearch";
import * as marketsService from "../../marketsService";

vi.mock("../../marketsService");

describe("StockSearch", () => {
  it("shows results after typing a query", async () => {
    const user = userEvent.setup();
    marketsService.search.mockResolvedValue([
      { symbol: "TCS.NS", name: "Tata Consultancy Services", sector: "IT" },
    ]);

    render(<StockSearch market="IN" />);
    await user.type(screen.getByPlaceholderText(/Search stocks/i), "tcs");

    await waitFor(() => {
      expect(screen.getByText("Tata Consultancy Services")).toBeInTheDocument();
    });
    expect(marketsService.search).toHaveBeenCalledWith("tcs", "IN");
  });

  it("shows 'No matches found' when the search returns an empty array", async () => {
    const user = userEvent.setup();
    marketsService.search.mockResolvedValue([]);

    render(<StockSearch market="IN" />);
    await user.type(screen.getByPlaceholderText(/Search stocks/i), "zzz");

    await waitFor(() => {
      expect(screen.getByText("No matches found")).toBeInTheDocument();
    });
  });

  it("clears results when the input is emptied", async () => {
    const user = userEvent.setup();
    marketsService.search.mockResolvedValue([
      { symbol: "TCS.NS", name: "Tata Consultancy Services", sector: "IT" },
    ]);

    render(<StockSearch market="IN" />);
    const input = screen.getByPlaceholderText(/Search stocks/i);
    await user.type(input, "tcs");
    await waitFor(() => {
      expect(screen.getByText("Tata Consultancy Services")).toBeInTheDocument();
    });

    await user.clear(input);

    expect(screen.queryByText("Tata Consultancy Services")).not.toBeInTheDocument();
  });
});