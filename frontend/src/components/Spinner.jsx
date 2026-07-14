// Small inline loading spinner, reused on buttons and panels
function Spinner({ size = 18, className = "" }) {
  return (
    <span
      className={`spinner ${className}`}
      style={{ width: size, height: size }}
      role="status"
      aria-label="Loading"
    />
  );
}

export default Spinner;
