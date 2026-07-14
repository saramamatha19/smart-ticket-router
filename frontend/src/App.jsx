// React hooks
import { useEffect, useState } from "react";

// Import CSS
import "./App.css";

// Import Components
import TicketForm from "./components/TicketForm";
import TicketResult from "./components/TicketResult";
import TicketHistory from "./components/TicketHistory";
import DashboardStats from "./components/DashboardStats";
import TicketChart from "./components/TicketChart";
import Toast from "./components/Toast";
import TimeSavings from "./components/TimeSavings";

// Import API functions
import { routeTicket, getTickets, getTicketStats } from "./services/api";

// Header icon
import { Bot } from "lucide-react";

function App() {

  // Store AI response
  const [result, setResult] = useState(null);

  // Store all tickets
  const [tickets, setTickets] = useState([]);

  // Store dashboard analytics (totals by priority/category/sentiment)
  const [stats, setStats] = useState(null);

  // Show loading while AI is processing
  const [loading, setLoading] = useState(false);

  // Store any error message
  const [error, setError] = useState("");

  // Toast notification shown after a routing attempt
  const [toast, setToast] = useState(null);

  // How long the most recent AI routing call took, in milliseconds
  const [lastRoutingTimeMs, setLastRoutingTimeMs] = useState(null);

  // Every AI routing time this session, used to compute the session average
  // shown in the AI Routing Speed card
  const [routingTimes, setRoutingTimes] = useState([]);

  // Function to fetch all tickets
  const loadTickets = async () => {
    try {
      const response = await getTickets();
      setTickets(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  // Function to fetch dashboard stats
  const loadStats = async () => {
    try {
      const response = await getTicketStats();
      setStats(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  // Load all tickets and stats when page opens
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount, no React Compiler in use
    loadTickets();
    loadStats();
  }, []);

  // Function called when user submits a ticket
  const handleRouteTicket = async (message) => {

    setLoading(true);
    setError("");

    try {

      // Time the full round trip so we can show a real AI routing time,
      // not an estimate, for the before/after comparison
      const startedAt = performance.now();

      // Call backend API
      const response = await routeTicket(message);

      const elapsedMs = performance.now() - startedAt;

      // Save AI result
      setResult(response.data);
      setLastRoutingTimeMs(elapsedMs);
      setRoutingTimes((prev) => [...prev, elapsedMs]);

      // Show success toast
      setToast({ type: "success", message: "Ticket routed successfully." });

      // Reload ticket history and dashboard stats
      await Promise.all([loadTickets(), loadStats()]);

    } catch (err) {

      console.error(err);

      setError("Failed to route ticket. Please try again.");
      setToast({ type: "error", message: "Something went wrong while routing the ticket." });

    } finally {

      setLoading(false);

    }

  };

  return (

    <div className="app-shell">

      {/* Header */}
      <header className="app-header">
        <div className="app-header-title">
          <Bot size={28} />
          <div>
            <h1>Smart Ticket Router</h1>
            <p>AI-powered support ticket classification &amp; routing</p>
          </div>
        </div>
      </header>

      <main className="container">

        {/* Dashboard Analytics */}
        <DashboardStats stats={stats} />

        {/* Real, measured AI routing time for this session */}
        <TimeSavings routingTimes={routingTimes} />

        {/* User Input + Distribution Chart — both fixed-height, always balanced */}
        <div className="top-grid">
          <TicketForm onRouteTicket={handleRouteTicket} loading={loading} error={error} />
          <TicketChart stats={stats} />
        </div>

        {/* AI Result — full width, only appears once a ticket has been routed */}
        <TicketResult result={result} routingTimeMs={lastRoutingTimeMs} />

        {/* Ticket History */}
        <TicketHistory tickets={tickets} />

      </main>

      {/* Toast Notification */}
      <Toast
        message={toast?.message}
        type={toast?.type}
        onClose={() => setToast(null)}
      />

    </div>

  );
}

export default App;
