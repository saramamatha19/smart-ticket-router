import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import TicketForm from "./TicketForm";

describe("TicketForm", () => {
  it("shows an inline validation error instead of a browser alert on empty submit", () => {
    const onRouteTicket = vi.fn();
    render(<TicketForm onRouteTicket={onRouteTicket} loading={false} />);

    fireEvent.click(screen.getByRole("button", { name: /route ticket/i }));

    expect(
      screen.getByText(/please enter a support message/i)
    ).toBeInTheDocument();
    expect(onRouteTicket).not.toHaveBeenCalled();
  });

  it("submits the message and clears the textarea", () => {
    const onRouteTicket = vi.fn();
    render(<TicketForm onRouteTicket={onRouteTicket} loading={false} />);

    const textarea = screen.getByPlaceholderText(/describe the customer's issue/i);
    fireEvent.change(textarea, { target: { value: "My WiFi keeps dropping" } });
    fireEvent.click(screen.getByRole("button", { name: /route ticket/i }));

    expect(onRouteTicket).toHaveBeenCalledWith("My WiFi keeps dropping");
    expect(textarea.value).toBe("");
  });

  it("disables the textarea and button while loading", () => {
    render(<TicketForm onRouteTicket={vi.fn()} loading={true} />);

    expect(screen.getByPlaceholderText(/describe the customer's issue/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /routing/i })).toBeDisabled();
  });

  it("surfaces a server-side error passed in via props", () => {
    render(<TicketForm onRouteTicket={vi.fn()} loading={false} error="Failed to route ticket." />);

    expect(screen.getByText("Failed to route ticket.")).toBeInTheDocument();
  });
});
