import { Navigate } from "react-router-dom";
import { useCustomerAuth } from "../context/useCustomerAuth";

// Wraps a route element so it's only reachable while logged in as a
// customer -- otherwise redirects to the customer login page. See
// ProtectedRoute for the equivalent guard on the admin route.
function CustomerProtectedRoute({ children }) {
  const { isAuthenticated } = useCustomerAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default CustomerProtectedRoute;
