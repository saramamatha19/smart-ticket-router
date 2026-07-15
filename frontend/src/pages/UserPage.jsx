// React hooks
import { useState } from "react";

// Import Components
import TicketForm from "../components/TicketForm";
import TicketResult from "../components/TicketResult";
import Toast from "../components/Toast";

// Import API functions
import { routeTicket } from "../services/api";

// Submitter-facing page: raise a ticket and see how the AI routed it.
// onRoutingTime reports each call's latency up to App, which feeds the
// AI Routing Speed card shown on the Admin Dashboard.
function UserPage({ onRoutingTime }) {

  // Store AI response(s) -- a message with multiple independent requests
  // routes to multiple entries, one per request
  const [results, setResults] = useState([]);

  // Show loading while AI is processing
  const [loading, setLoading] = useState(false);

  // Store any error message
  const [error, setError] = useState("");

  // Toast notification shown after a routing attempt
  const [toast, setToast] = useState(null);

  // How long the most recent AI routing call took, in milliseconds
  const [lastRoutingTimeMs, setLastRoutingTimeMs] = useState(null);

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

      // Save AI result(s)
      setResults(response.data);
      setLastRoutingTimeMs(elapsedMs);
      onRoutingTime(elapsedMs);

      // Show success toast, calling out a multi-intent split
      const toastMessage =
        response.data.length > 1
          ? `Ticket split into ${response.data.length} separate requests and routed.`
          : "Ticket routed successfully.";
      setToast({ type: "success", message: toastMessage });

    } catch (err) {

      console.error(err);

      setError("Failed to route ticket. Please try again.");
      setToast({ type: "error", message: "Something went wrong while routing the ticket." });

    } finally {

      setLoading(false);

    }

  };

  return (

    <>

      {/* User Input */}
      <TicketForm onRouteTicket={handleRouteTicket} loading={loading} error={error} />

      {/* AI Result(s) — only appears once a ticket has been routed */}
      <TicketResult results={results} routingTimeMs={lastRoutingTimeMs} />

      {/* Toast Notification */}
      <Toast
        message={toast?.message}
        type={toast?.type}
        onClose={() => setToast(null)}
      />

    </>

  );
}

export default UserPage;
