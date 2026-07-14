import { useEffect } from "react";
import { CheckCircle2, XCircle } from "lucide-react";

// Small auto-dismissing toast for success/error feedback after actions
function Toast({ message, type = "success", onClose }) {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(onClose, 3500);
    return () => clearTimeout(timer);
  }, [message, onClose]);

  if (!message) return null;

  const Icon = type === "error" ? XCircle : CheckCircle2;

  return (
    <div className={`toast toast-${type}`} role="status">
      <Icon size={18} />
      <span>{message}</span>
    </div>
  );
}

export default Toast;
