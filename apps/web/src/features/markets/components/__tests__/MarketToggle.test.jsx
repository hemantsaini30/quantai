// FILE LOCATION: quantai/apps/web/src/features/markets/components/__tests__/MarketToggle.test.jsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import MarketToggle from "../MarketToggle";

describe("MarketToggle", () => {
  it("calls onChange with 'US' when the United States button is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<MarketToggle market="IN" onChange={onChange} />);
    await user.click(screen.getByText("United States"));

    expect(onChange).toHaveBeenCalledWith("US");
  });

  it("calls onChange with 'IN' when the India button is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<MarketToggle market="US" onChange={onChange} />);
    await user.click(screen.getByText("India"));

    expect(onChange).toHaveBeenCalledWith("IN");
  });
});