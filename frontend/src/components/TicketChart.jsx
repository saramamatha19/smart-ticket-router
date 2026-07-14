import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const METRICS = [
  { key: "by_category", label: "Category" },
  { key: "by_priority", label: "Priority" },
  { key: "by_sentiment", label: "Sentiment" },
];

const COLORS = ["#4f46e5", "#0ea5e9", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6"];

// One switchable bar chart covering category / priority / sentiment distribution
function TicketChart({ stats }) {
  const [metric, setMetric] = useState("by_category");

  const data = Object.entries(stats?.[metric] || {}).map(([name, count]) => ({
    name,
    count,
  }));

  return (
    <div className="card chart-card">
      <div className="card-header">
        <h2>Ticket Distribution</h2>
        <div className="chart-tabs">
          {METRICS.map((m) => (
            <button
              key={m.key}
              type="button"
              className={`chart-tab ${metric === m.key ? "active" : ""}`}
              onClick={() => setMetric(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {data.length === 0 ? (
        <div className="chart-body chart-empty">
          <p className="empty-state">No data yet. Route a ticket to see the chart.</p>
        </div>
      ) : (
        <div className="chart-body">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "var(--text-muted)" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "var(--text-muted)" }} />
              <Tooltip
                contentStyle={{
                  borderRadius: 10,
                  border: "1px solid var(--border)",
                  fontSize: 13,
                }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default TicketChart;
