// Colored pill used for priority and sentiment values
const PRIORITY_STYLES = {
  High: "badge-high",
  Medium: "badge-medium",
  Low: "badge-low",
};

const SENTIMENT_STYLES = {
  Positive: "badge-positive",
  Neutral: "badge-neutral",
  Angry: "badge-angry",
};

function Badge({ label, type = "priority" }) {
  if (!label) return null;

  const styles = type === "sentiment" ? SENTIMENT_STYLES : PRIORITY_STYLES;
  const variant = styles[label] || "badge-default";

  return <span className={`badge ${variant}`}>{label}</span>;
}

export default Badge;
