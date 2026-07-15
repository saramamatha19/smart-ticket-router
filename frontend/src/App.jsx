// React hooks
import { useState } from "react";

// Routing
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";

// Import CSS
import "./App.css";

// Pages
import UserPage from "./pages/UserPage";
import AdminPage from "./pages/AdminPage";

// Header icon
import { Bot } from "lucide-react";

function App() {

  // Every AI routing time this session, lifted up here (rather than kept
  // inside UserPage) so it survives navigating to the Admin Dashboard,
  // where the AI Routing Speed card is shown.
  const [routingTimes, setRoutingTimes] = useState([]);

  const recordRoutingTime = (ms) => {
    setRoutingTimes((prev) => [...prev, ms]);
  };

  return (

    <BrowserRouter>

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
              <NavLink
                to="/"
                end
                className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
              >
                Submit a Ticket
              </NavLink>
              <NavLink
                to="/admin"
                className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
              >
                Admin Dashboard
              </NavLink>
            </nav>
          </div>
        </header>

        <main className="container">
          <Routes>
            <Route path="/" element={<UserPage onRoutingTime={recordRoutingTime} />} />
            <Route path="/admin" element={<AdminPage routingTimes={routingTimes} />} />
          </Routes>
        </main>

      </div>

    </BrowserRouter>

  );
}

export default App;
