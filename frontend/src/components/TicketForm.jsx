// React state hook
import { useState } from "react";
import { Send } from "lucide-react";
import Spinner from "./Spinner";

// TicketForm Component
function TicketForm({ onRouteTicket, loading, error }) {

  // Store the user's input
  const [message, setMessage] = useState("");

  // Inline validation message (replaces browser alert())
  const [validationError, setValidationError] = useState("");

  // Called when user clicks the button
  const handleSubmit = (e) => {

    // Prevent page refresh
    e.preventDefault();

    // Check if input is empty
    if (!message.trim()) {
      setValidationError("Please enter a support message before submitting.");
      return;
    }

    setValidationError("");

    // Send the message to the parent component
    onRouteTicket(message);

    // Clear the textbox after sending
    setMessage("");
  };

  return (
    <div className="card">

      <h2>Enter Support Message</h2>

      <form onSubmit={handleSubmit}>

        {/* Text area for customer message */}
        <textarea
          rows="6"
          placeholder="Describe the customer's issue..."
          value={message}
          disabled={loading}
          onChange={(e) => {
            setMessage(e.target.value);
            if (validationError) setValidationError("");
          }}
        />

        {/* Inline validation message, or the server-side error if the request failed */}
        {(validationError || error) && (
          <p className="field-error">{validationError || error}</p>
        )}

        {/* Submit Button */}
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? (
            <>
              <Spinner size={16} /> Routing...
            </>
          ) : (
            <>
              <Send size={16} /> Route Ticket
            </>
          )}
        </button>

      </form>

    </div>
  );
}

export default TicketForm;
