// FILE LOCATION: quantai/apps/web/src/features/markets/components/__tests__/SectorPerformance.test.jsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SectorPerformance from "../SectorPerformance";

describe("SectorPerformance", () => {
  it("renders every sector name and its formatted percent change", () => {
    render(
      <SectorPerformance
        sectors={[
          { sector: "IT", average_percent_change: 1.25 },
          { sector: "Energy", average_percent_change: -0.8 },
        ]}
      />
    );

    expect(screen.getByText("IT")).toBeInTheDocument();
    expect(screen.getByText("+1.25%")).toBeInTheDocument();
    expect(screen.getByText("Energy")).toBeInTheDocument();
    expect(screen.getByText("-0.80%")).toBeInTheDocument();
  });

  it("does not crash when given an empty sectors array", () => {
    render(<SectorPerformance sectors={[]} />);

    expect(screen.getByText("Sector Performance")).toBeInTheDocument();
  });
});