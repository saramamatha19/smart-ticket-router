import { createContext } from "react";

// Single admin login state, shared via AuthProvider/useAuth. Split into
// its own file (no components here) so react-refresh doesn't complain
// about non-component exports living alongside AuthProvider.
export const AuthContext = createContext(null);
