// React hooks
import { useState } from "react";

// Routing
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from "react-router-dom";

// Import CSS
import "./App.css";

// Pages
import UserPage from "./pages/UserPage";
import AdminPage from "./pages/AdminPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import CustomerLoginPage from "./pages/CustomerLoginPage";
import CustomerRegisterPage from "./pages/CustomerRegisterPage";
import MyTicketsPage from "./pages/MyTicketsPage";

// Admin auth
import { AuthProvider } from "./context/AuthProvider";
import { useAuth } from "./context/useAuth";
import ProtectedRoute from "./components/ProtectedRoute";

// Customer auth
import { CustomerAuthProvider } from "./context/CustomerAuthProvider";
import { useCustomerAuth } from "./context/useCustomerAuth";
import CustomerProtectedRoute from "./components/CustomerProtectedRoute";

// Header icons
import { Bot, LogOut } from "lucide-react";

function AppShell() {

  // Every AI routing time this session, lifted up here (rather than kept
  // inside UserPage) so it survives navigating to the Admin Dashboard,
  // where the AI Routing Speed card is shown.
  const [routingTimes, setRoutingTimes] = useState([]);

  const { isAuthenticated: isAdmin, logout: adminLogout } = useAuth();
  const { isAuthenticated: isCustomer, logout: customerLogout } = useCustomerAuth();
  const navigate = useNavigate();

  const recordRoutingTime = (ms) => {
    setRoutingTimes((prev) => [...prev, ms]);
  };

  const handleAdminLogout = () => {
    adminLogout();
    navigate("/");
  };

  const handleCustomerLogout = () => {
    customerLogout();
    navigate("/login");
  };

  return (

    <div className="app-shell">

      {/* Header */}
      <header className="app-header">
        <div className="app-header-inner">
          <div className="app-header-title">
            <Bot size={28} />
            <div>
              <h1>Smart Ticket Router</h1>
              <p>AI-powered support ticket classification &amp; routing</p>
            </div>
          </div>

          {/* Page navigation */}
          <nav className="app-nav">
            {isCustomer ? (
              <>
                <NavLink
                  to="/"
                  end
                  className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
                >
                  Submit a Ticket
                </NavLink>
                <NavLink
                  to="/my-tickets"
                  className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
                >
                  My Tickets
                </NavLink>
              </>
            ) : (
              <>
                <NavLink
                  to="/login"
                  className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
                >
                  Log In
                </NavLink>
                <NavLink
                  to="/register"
                  className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
                >
                  Sign Up
                </NavLink>
              </>
            )}

            <NavLink
              to="/admin"
              className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
            >
              Admin Dashboard
            </NavLink>

            {/* Only shown once logged in as a customer */}
            {isCustomer && (
              <button type="button" className="btn-ghost" onClick={handleCustomerLogout}>
                <LogOut size={14} /> Log Out
              </button>
            )}

            {/* Only shown once logged in as the admin */}
            {isAdmin && (
              <button type="button" className="btn-ghost" onClick={handleAdminLogout}>
                <LogOut size={14} /> Admin Log Out
              </button>
            )}
          </nav>
        </div>
      </header>

      <main className="container">
        <Routes>
          <Route
            path="/"
            element={
              <CustomerProtectedRoute>
                <UserPage onRoutingTime={recordRoutingTime} />
              </CustomerProtectedRoute>
            }
          />
          <Route path="/login" element={<CustomerLoginPage />} />
          <Route path="/register" element={<CustomerRegisterPage />} />
          <Route
            path="/my-tickets"
            element={
              <CustomerProtectedRoute>
                <MyTicketsPage />
              </CustomerProtectedRoute>
            }
          />
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminPage routingTimes={routingTimes} />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>

    </div>

  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CustomerAuthProvider>
          <AppShell />
        </CustomerAuthProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
