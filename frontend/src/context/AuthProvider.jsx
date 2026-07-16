import { useCallback, useEffect, useState } from "react";
import { AuthContext } from "./AuthContext";
import { adminLogin, ADMIN_TOKEN_STORAGE_KEY } from "../services/api";

// Provides the admin's login state to the whole app: whether they're
// logged in, and login()/logout() to change it. There's a single admin
// account (see backend ADMIN_USERNAME/ADMIN_PASSWORD), so this only ever
// tracks "logged in or not" -- no user object, no roles. Separate from
// CustomerAuthProvider, which tracks the (real, DB-backed) customer session.
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY));

  // A 401 from any admin API call (see services/api.js) means the token
  // expired or was revoked -- drop it here too so isAuthenticated flips
  // to false and ProtectedRoute bounces the user back to /admin/login.
  useEffect(() => {
    const handleUnauthorized = () => setToken(null);
    window.addEventListener("admin-auth:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("admin-auth:unauthorized", handleUnauthorized);
  }, []);

  const login = useCallback(async (username, password) => {
    const response = await adminLogin(username, password);
    const { access_token } = response.data;
    localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, access_token);
    setToken(access_token);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated: Boolean(token), login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
