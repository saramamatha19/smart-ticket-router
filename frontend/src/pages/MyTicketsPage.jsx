// React hooks
import { useEffect, useState } from "react";

// Components
import TicketHistory from "../components/TicketHistory";

// API
import { getMyTickets } from "../services/api";

// Customer-facing page: only the tickets this customer submitted
// themselves (see GET /tickets/mine) -- not the admin's full history.
function MyTicketsPage() {

  const [tickets, setTickets] = useState([]);

  useEffect(() => {
    getMyTickets()
      .then((response) => setTickets(response.data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <>
      <h2 className="page-title">My Tickets</h2>
      <TicketHistory tickets={tickets} />
    </>
  );
}

export default MyTicketsPage;
