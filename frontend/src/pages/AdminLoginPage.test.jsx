import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import AdminLoginPage from "./AdminLoginPage";
import { AuthProvider } from "../context/AuthProvider";
import * as api from "../services/api";

vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return { ...actual, adminLogin: vi.fn() };
});

function renderLoginPage() {
  render(
    <MemoryRouter initialEntries={["/admin/login"]}>
      <AuthProvider>
        <Routes>
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin" element={<div>Admin Dashboard Page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("AdminLoginPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("logs in and navigates to the admin dashboard on success", async () => {
    api.adminLogin.mockResolvedValue({ data: { access_token: "fake-token", token_type: "bearer" } });

    renderLoginPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "admin123" } });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => {
      expect(screen.getByText("Admin Dashboard Page")).toBeInTheDocument();
    });

    expect(api.adminLogin).toHaveBeenCalledWith("admin", "admin123");
  });

  it("shows an error message and stays on the page when login fails", async () => {
    api.adminLogin.mockRejectedValue(new Error("Request failed with status code 401"));

    renderLoginPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    expect(await screen.findByText(/incorrect username or password/i)).toBeInTheDocument();
  });
});
