import { createContext } from "react";

// Customer login state, shared via CustomerAuthProvider/useCustomerAuth.
// Split into its own file (no components here) so react-refresh doesn't
// complain about non-component exports living alongside the provider.
export const CustomerAuthContext = createContext(null);
