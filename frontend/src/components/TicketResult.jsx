import { useState } from "react";
import { AlertTriangle, Clock3, Copy, Check, Tag, Users, Eye } from "lucide-react";
import Badge from "./Badge";

// Visual meter for the AI's confidence score (0-100)
function ConfidenceMeter({ value }) {
  const tone = value >= 80 ? "high" : value >= 50 ? "medium" : "low";

  return (
    <div className="confidence-meter">
      <div className="confidence-track">
        <div
          className={`confidence-fill confidence-${tone}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="confidence-value">{value}%</span>
    </div>
  );
}

// TicketResult Component — renders the full AI analysis for the latest ticket
function TicketResult({ result, routingTimeMs }) {

  // Whether the "Copy" button was just clicked (for button feedback)
  const [copied, setCopied] = useState(false);

  // Don't show anything until we have a result
  if (!result) {
    return null;
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.suggested_reply);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card result-card">

      <div className="card-header">
        <h2>AI Analysis</h2>
        <div className="result-header-meta">
          {routingTimeMs != null && (
            <span className="routing-time">
              <Clock3 size={13} /> Routed in {(routingTimeMs / 1000).toFixed(1)}s
            </span>
          )}
          <Badge label={result.priority} type="priority" />
        </div>
      </div>

      {result.escalation_needed && (
        <div className="escalation-banner">
          <AlertTriangle size={18} />
          <span>Escalation recommended — this ticket needs immediate attention.</span>
        </div>
      )}

      {result.needs_human_review && (
        <div className="review-banner">
          <Eye size={18} />
          <span>Low confidence ({result.confidence}%) — a human should double-check this classification.</span>
        </div>
      )}

      <p className="result-summary">{result.summary}</p>

      <div className="result-grid">

        <div className="result-item">
          <span className="result-label"><Tag size={14} /> Category</span>
          <span className="result-value">{result.category}</span>
        </div>

        <div className="result-item">
          <span className="result-label"><Users size={14} /> Assigned Team</span>
          <span className="result-value">{result.assigned_team}</span>
        </div>

        <div className="result-item">
          <span className="result-label"><Clock3 size={14} /> Resolution ETA</span>
          <span className="result-value">{result.estimated_resolution_time}</span>
        </div>

        <div className="result-item">
          <span className="result-label">Sentiment</span>
          <Badge label={result.sentiment} type="sentiment" />
        </div>

      </div>

      <div className="confidence-row">
        <span className="result-label">AI Confidence</span>
        <ConfidenceMeter value={result.confidence} />
      </div>

      {result.keywords?.length > 0 && (
        <div className="keywords-row">
          {result.keywords.map((word) => (
            <span key={word} className="keyword-chip">{word}</span>
          ))}
        </div>
      )}

      <div className="reason-box">
        <strong>Why:</strong> {result.reason}
      </div>

      <div className="reply-box">
        <div className="reply-header">
          <strong>Suggested Reply</strong>
          <button type="button" className="btn-ghost" onClick={handleCopy}>
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
        <p>{result.suggested_reply}</p>
      </div>

    </div>
  );
}

export default TicketResult;
