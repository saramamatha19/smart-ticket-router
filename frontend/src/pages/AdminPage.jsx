// React hooks
import { useEffect, useState } from "react";

// Import Components
import DashboardStats from "../components/DashboardStats";
import TicketChart from "../components/TicketChart";
import TicketHistory from "../components/TicketHistory";
import TimeSavings from "../components/TimeSavings";

// Import API functions
import { getTickets, getTicketStats } from "../services/api";

// Admin-facing page: monitor routing analytics and browse ticket history.
function AdminPage({ routingTimes }) {

  // Store all tickets
  const [tickets, setTickets] = useState([]);

  // Store dashboard analytics (totals by priority/category/sentiment)
  const [stats, setStats] = useState(null);

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

  // Load all tickets and stats when the page opens
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount, no React Compiler in use
    loadTickets();
    loadStats();
  }, []);

  return (

    <>

      {/* Dashboard Analytics */}
      <DashboardStats stats={stats} />

      {/* Real, measured AI routing time across this session */}
      <TimeSavings routingTimes={routingTimes} />

      {/* Distribution Chart */}
      <TicketChart stats={stats} />

      {/* Ticket History */}
      <TicketHistory tickets={tickets} />

    </>

  );
}

export default AdminPage;
