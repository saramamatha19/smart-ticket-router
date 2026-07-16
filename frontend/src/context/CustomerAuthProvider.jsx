import { useCallback, useEffect, useState } from "react";
import { CustomerAuthContext } from "./CustomerAuthContext";
import { customerLogin, registerCustomer, CUSTOMER_TOKEN_STORAGE_KEY } from "../services/api";

// Provides the logged-in customer's session to the whole app: whether
// they're logged in, and register()/login()/logout() to change it.
// Separate from AuthProvider, which tracks the single hardcoded admin
// account -- a customer and the admin can be logged in at the same time,
// each with their own token.
export function CustomerAuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(CUSTOMER_TOKEN_STORAGE_KEY));

  // A 401 from any customer API call (see services/api.js) means the
  // token expired or was revoked -- drop it here too so isAuthenticated
  // flips to false and CustomerProtectedRoute bounces back to /login.
  useEffect(() => {
    const handleUnauthorized = () => setToken(null);
    window.addEventListener("customer-auth:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("customer-auth:unauthorized", handleUnauthorized);
  }, []);

  const register = useCallback(async (email, password) => {
    const response = await registerCustomer(email, password);
    const { access_token } = response.data;
    localStorage.setItem(CUSTOMER_TOKEN_STORAGE_KEY, access_token);
    setToken(access_token);
  }, []);

  const login = useCallback(async (email, password) => {
    const response = await customerLogin(email, password);
    const { access_token } = response.data;
    localStorage.setItem(CUSTOMER_TOKEN_STORAGE_KEY, access_token);
    setToken(access_token);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(CUSTOMER_TOKEN_STORAGE_KEY);
    setToken(null);
  }, []);

  return (
    <CustomerAuthContext.Provider value={{ isAuthenticated: Boolean(token), register, login, logout }}>
      {children}
    </CustomerAuthContext.Provider>
  );
}
