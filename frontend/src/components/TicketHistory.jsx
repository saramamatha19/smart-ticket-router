import { useMemo, useState } from "react";
import { Search, Download, ArrowUp, ArrowDown, Eye } from "lucide-react";
import Badge from "./Badge";

// Used to sort priority by severity instead of alphabetically
const PRIORITY_ORDER = { High: 3, Medium: 2, Low: 1 };

// Builds a CSV file from the currently visible tickets and downloads it
function downloadCsv(tickets) {
  const headers = [
    "ID",
    "Message",
    "Category",
    "Priority",
    "Assigned Team",
    "Needs Human Review",
    "Created At",
  ];

  const rows = tickets.map((t) => [
    t.id,
    `"${(t.message || "").replace(/"/g, '""')}"`,
    t.category,
    t.priority,
    t.assigned_team,
    t.needs_human_review ? "Yes" : "No",
    t.created_at,
  ]);

  const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = "ticket-history.csv";
  link.click();
  URL.revokeObjectURL(url);
}

// Small header button that shows the active sort direction
function SortIcon({ field, sortField, sortDir }) {
  if (sortField !== field) return null;
  return sortDir === "asc" ? <ArrowUp size={13} /> : <ArrowDown size={13} />;
}

// TicketHistory Component
function TicketHistory({ tickets }) {

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");
  const [reviewOnly, setReviewOnly] = useState(false);
  const [sortField, setSortField] = useState("id");
  const [sortDir, setSortDir] = useState("desc");

  const categories = useMemo(
    () => ["All", ...new Set((tickets || []).map((t) => t.category))],
    [tickets]
  );

  const priorities = ["All", "High", "Medium", "Low"];

  const filtered = useMemo(() => {
    let result = tickets || [];

    if (search.trim()) {
      const query = search.toLowerCase();
      result = result.filter((t) => t.message?.toLowerCase().includes(query));
    }

    if (categoryFilter !== "All") {
      result = result.filter((t) => t.category === categoryFilter);
    }

    if (priorityFilter !== "All") {
      result = result.filter((t) => t.priority === priorityFilter);
    }

    if (reviewOnly) {
      result = result.filter((t) => t.needs_human_review);
    }

    return [...result].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (sortField === "priority") {
        valA = PRIORITY_ORDER[valA] || 0;
        valB = PRIORITY_ORDER[valB] || 0;
      }

      if (valA < valB) return sortDir === "asc" ? -1 : 1;
      if (valA > valB) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }, [tickets, search, categoryFilter, priorityFilter, reviewOnly, sortField, sortDir]);

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  // If there are no tickets, show a message
  if (!tickets || tickets.length === 0) {
    return (
      <div className="card">
        <h2>Ticket History</h2>
        <div className="empty-state">
          <p>No tickets yet.</p>
          <span>Route your first ticket above to see it appear here.</span>
        </div>
      </div>
    );
  }

  const reviewCount = (tickets || []).filter((t) => t.needs_human_review).length;

  return (
    <div className="card">

      <div className="card-header">
        <h2>Ticket History</h2>
        <button type="button" className="btn-ghost" onClick={() => downloadCsv(filtered)}>
          <Download size={14} /> Export CSV
        </button>
      </div>

      <div className="history-toolbar">

        <div className="search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search ticket messages..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          {categories.map((c) => (
            <option key={c} value={c}>{c === "All" ? "All Categories" : c}</option>
          ))}
        </select>

        <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
          {priorities.map((p) => (
            <option key={p} value={p}>{p === "All" ? "All Priorities" : p}</option>
          ))}
        </select>

        <label className="review-only-toggle">
          <input
            type="checkbox"
            checked={reviewOnly}
            onChange={(e) => setReviewOnly(e.target.checked)}
          />
          <Eye size={14} /> Needs review only ({reviewCount})
        </label>

      </div>

      <div className="table-wrapper">
        <table>

          <thead>
            <tr>
              <th onClick={() => toggleSort("id")}>
                ID <SortIcon field="id" sortField={sortField} sortDir={sortDir} />
              </th>
              <th>Message</th>
              <th onClick={() => toggleSort("category")}>
                Category <SortIcon field="category" sortField={sortField} sortDir={sortDir} />
              </th>
              <th onClick={() => toggleSort("priority")}>
                Priority <SortIcon field="priority" sortField={sortField} sortDir={sortDir} />
              </th>
              <th>Assigned Team</th>
              <th onClick={() => toggleSort("needs_human_review")}>
                Review <SortIcon field="needs_human_review" sortField={sortField} sortDir={sortDir} />
              </th>
            </tr>
          </thead>

          <tbody>
            {filtered.map((ticket) => (
              <tr key={ticket.id} className={ticket.needs_human_review ? "row-needs-review" : ""}>
                <td>{ticket.id}</td>
                <td className="message-cell" title={ticket.message}>{ticket.message}</td>
                <td>{ticket.category}</td>
                <td><Badge label={ticket.priority} type="priority" /></td>
                <td>{ticket.assigned_team}</td>
                <td>
                  {ticket.needs_human_review && (
                    <span className="review-flag" title={`Confidence ${ticket.confidence}% — below the review threshold`}>
                      <Eye size={14} /> Review
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>

        </table>

        {filtered.length === 0 && (
          <p className="empty-state">No tickets match your filters.</p>
        )}
      </div>

    </div>
  );
}

export default TicketHistory;
