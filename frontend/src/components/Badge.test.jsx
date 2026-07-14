import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Badge from "./Badge";

describe("Badge", () => {
  it("renders nothing when no label is given", () => {
    const { container } = render(<Badge label={undefined} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("applies the priority color class matching the label", () => {
    render(<Badge label="High" type="priority" />);
    const badge = screen.getByText("High");
    expect(badge).toHaveClass("badge-high");
  });

  it("applies the sentiment color class matching the label", () => {
    render(<Badge label="Angry" type="sentiment" />);
    const badge = screen.getByText("Angry");
    expect(badge).toHaveClass("badge-angry");
  });

  it("falls back to a default style for an unrecognized value", () => {
    render(<Badge label="Unexpected" type="sentiment" />);
    const badge = screen.getByText("Unexpected");
    expect(badge).toHaveClass("badge-default");
  });
});
