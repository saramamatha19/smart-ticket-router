import { Inbox, AlertTriangle, Clock3, CheckCircle2, Eye } from "lucide-react";

// Top-of-dashboard summary cards, backed by GET /tickets/stats
function DashboardStats({ stats }) {
  if (!stats) return null;

  const { total = 0, by_priority = {}, by_category = {}, needs_human_review_count = 0 } = stats;

  const priorityCards = [
    { label: "Total Tickets", value: total, icon: Inbox, tone: "primary" },
    { label: "High Priority", value: by_priority.High || 0, icon: AlertTriangle, tone: "high" },
    { label: "Medium Priority", value: by_priority.Medium || 0, icon: Clock3, tone: "medium" },
    { label: "Low Priority", value: by_priority.Low || 0, icon: CheckCircle2, tone: "low" },
    { label: "Needs Human Review", value: needs_human_review_count, icon: Eye, tone: "medium" },
  ];

  const categoryEntries = Object.entries(by_category);

  return (
    <section className="stats-section">
      <div className="stats-grid">
        {priorityCards.map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className={`stat-card stat-${tone}`}>
            <div className="stat-icon">
              <Icon size={20} />
            </div>
            <div>
              <p className="stat-value">{value}</p>
              <p className="stat-label">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {categoryEntries.length > 0 && (
        <div className="stats-grid stats-grid-secondary">
          {categoryEntries.map(([label, value]) => (
            <div key={label} className="stat-card stat-neutral">
              <p className="stat-value">{value}</p>
              <p className="stat-label">{label}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default DashboardStats;
