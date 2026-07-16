import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import CustomerLoginPage from "./CustomerLoginPage";
import { CustomerAuthProvider } from "../context/CustomerAuthProvider";
import * as api from "../services/api";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return { ...actual, customerLogin: vi.fn() };
});

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <CustomerAuthProvider>
        <Routes>
          <Route path="/login" element={<CustomerLoginPage />} />
          <Route path="/" element={<div>Submit a Ticket Page</div>} />
        </Routes>
      </CustomerAuthProvider>
    </MemoryRouter>
  );
}

describe("CustomerLoginPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("logs in and navigates to the ticket submission page on success", async () => {
    api.customerLogin.mockResolvedValue({ data: { access_token: "fake-token", token_type: "bearer" } });

    renderPage();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "alice@example.com" } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: "hunter22" } });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => {
      expect(screen.getByText("Submit a Ticket Page")).toBeInTheDocument();
    });

    expect(api.customerLogin).toHaveBeenCalledWith("alice@example.com", "hunter22");
  });

  it("shows an error message and stays on the page when login fails", async () => {
    api.customerLogin.mockRejectedValue(new Error("Request failed with status code 401"));

    renderPage();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "alice@example.com" } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    expect(await screen.findByText(/incorrect email or password/i)).toBeInTheDocument();
  });
});
