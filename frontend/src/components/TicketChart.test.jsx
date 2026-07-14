import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import TicketChart from "./TicketChart";

describe("TicketChart", () => {
  it("shows an empty state with no stats yet", () => {
    render(<TicketChart stats={null} />);
    expect(screen.getByText(/no data yet/i)).toBeInTheDocument();
  });

  it("lets you switch between category, priority, and sentiment tabs", () => {
    render(<TicketChart stats={null} />);

    const priorityTab = screen.getByRole("button", { name: "Priority" });
    fireEvent.click(priorityTab);
    expect(priorityTab).toHaveClass("active");

    const sentimentTab = screen.getByRole("button", { name: "Sentiment" });
    fireEvent.click(sentimentTab);
    expect(sentimentTab).toHaveClass("active");
    expect(priorityTab).not.toHaveClass("active");
  });
});
