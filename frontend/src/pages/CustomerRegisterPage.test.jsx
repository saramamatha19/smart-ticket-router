import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import CustomerRegisterPage from "./CustomerRegisterPage";
import { CustomerAuthProvider } from "../context/CustomerAuthProvider";
import * as api from "../services/api";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return { ...actual, registerCustomer: vi.fn() };
});

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/register"]}>
      <CustomerAuthProvider>
        <Routes>
          <Route path="/register" element={<CustomerRegisterPage />} />
          <Route path="/" element={<div>Submit a Ticket Page</div>} />
        </Routes>
      </CustomerAuthProvider>
    </MemoryRouter>
  );
}

function fillForm({ email = "alice@example.com", password = "hunter22", confirm = password }) {
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: password } });
  fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: confirm } });
}

describe("CustomerRegisterPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("registers and navigates to the ticket submission page on success", async () => {
    api.registerCustomer.mockResolvedValue({ data: { access_token: "fake-token", token_type: "bearer" } });

    renderPage();
    fillForm({});
    fireEvent.click(screen.getByRole("button", { name: /sign up/i }));

    await waitFor(() => {
      expect(screen.getByText("Submit a Ticket Page")).toBeInTheDocument();
    });

    expect(api.registerCustomer).toHaveBeenCalledWith("alice@example.com", "hunter22");
  });

  it("rejects a password shorter than 8 characters without calling the API", async () => {
    renderPage();
    fillForm({ password: "short", confirm: "short" });
    fireEvent.click(screen.getByRole("button", { name: /sign up/i }));

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument();
    expect(api.registerCustomer).not.toHaveBeenCalled();
  });

  it("rejects mismatched passwords without calling the API", async () => {
    renderPage();
    fillForm({ password: "hunter22", confirm: "somethingelse" });
    fireEvent.click(screen.getByRole("button", { name: /sign up/i }));

    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
    expect(api.registerCustomer).not.toHaveBeenCalled();
  });

  it("shows a specific error when the email is already registered", async () => {
    api.registerCustomer.mockRejectedValue({ response: { status: 409 } });

    renderPage();
    fillForm({});
    fireEvent.click(screen.getByRole("button", { name: /sign up/i }));

    expect(await screen.findByText(/already exists/i)).toBeInTheDocument();
  });
});
