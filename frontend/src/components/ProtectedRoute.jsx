import { Navigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

// Wraps a route element so it's only reachable while logged in as the
// admin -- otherwise redirects to the admin login page. See
// CustomerProtectedRoute for the equivalent guard on customer routes.
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
