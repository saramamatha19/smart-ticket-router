import { Zap, Clock3 } from "lucide-react";

// Real, measured AI routing time for this session. No assumed manual
// baseline is shown here -- manual triage time varies by person, so
// that comparison is made verbally during the demo instead of
// hard-coding a number nobody actually measured.
function TimeSavings({ routingTimes }) {

  if (!routingTimes || routingTimes.length === 0) {
    return (
      <div className="card time-savings-card">
        <div className="card-header">
          <h2><Zap size={18} /> AI Routing Speed</h2>
        </div>
        <p className="empty-state">Route a ticket to see how fast the AI responds.</p>
      </div>
    );
  }

  const avgMs = routingTimes.reduce((sum, ms) => sum + ms, 0) / routingTimes.length;
  const avgSeconds = avgMs / 1000;
  const lastSeconds = routingTimes[routingTimes.length - 1] / 1000;

  return (
    <div className="card time-savings-card">

      <div className="card-header">
        <h2><Zap size={18} /> AI Routing Speed</h2>
      </div>

      <div className="time-savings-grid">

        <div className="time-stat">
          <span className="result-label"><Clock3 size={14} /> Last Ticket</span>
          <span className="time-value time-value-ai">{lastSeconds.toFixed(2)}s</span>
        </div>

        <div className="time-stat time-stat-highlight">
          <span className="result-label">Session Average ({routingTimes.length} ticket{routingTimes.length === 1 ? "" : "s"})</span>
          <span className="time-value time-value-ai">{avgSeconds.toFixed(2)}s</span>
        </div>

      </div>

    </div>
  );
}

export default TimeSavings;
