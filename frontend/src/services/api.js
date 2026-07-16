// Import axios library
import axios from "axios";

// Backend API URL (set in .env as VITE_API_URL, falls back to local dev)
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
});

// localStorage keys for each JWT — shared with the two auth contexts so
// they read/write the exact same slots. Two separate sessions (admin,
// customer) can be logged in at once, each with its own token.
export const ADMIN_TOKEN_STORAGE_KEY = "admin_auth_token";
export const CUSTOMER_TOKEN_STORAGE_KEY = "customer_auth_token";

// Which endpoint needs which token -- exact relative paths, so
// /tickets/mine (customer) is never confused with /tickets (admin).
const ADMIN_ENDPOINTS = new Set(["/tickets", "/tickets/stats"]);
const CUSTOMER_ENDPOINTS = new Set(["/route-ticket", "/tickets/mine"]);

// Attach the right bearer token, if one is stored, to every outgoing request.
API.interceptors.request.use((config) => {
  let tokenKey = null;
  if (ADMIN_ENDPOINTS.has(config.url)) tokenKey = ADMIN_TOKEN_STORAGE_KEY;
  else if (CUSTOMER_ENDPOINTS.has(config.url)) tokenKey = CUSTOMER_TOKEN_STORAGE_KEY;

  const token = tokenKey && localStorage.getItem(tokenKey);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A rejected/expired token means the stored session is no longer valid --
// clear it and let the matching auth context know, so a stale screen
// doesn't sit there silently failing every request.
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url;
      if (ADMIN_ENDPOINTS.has(url)) {
        localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
        window.dispatchEvent(new Event("admin-auth:unauthorized"));
      } else if (CUSTOMER_ENDPOINTS.has(url)) {
        localStorage.removeItem(CUSTOMER_TOKEN_STORAGE_KEY);
        window.dispatchEvent(new Event("customer-auth:unauthorized"));
      }
    }
    return Promise.reject(error);
  }
);

// Log in as the admin user, returning a JWT to store for later requests
export const adminLogin = (username, password) => {
  return API.post("/admin/login", { username, password });
};

// Register a new customer account, returning a JWT to store for later requests
export const registerCustomer = (email, password) => {
  return API.post("/register", { email, password });
};

// Log in as an existing customer, returning a JWT to store for later requests
export const customerLogin = (email, password) => {
  return API.post("/login", { email, password });
};

// Route a support ticket (requires a logged-in customer)
export const routeTicket = (message) => {
  return API.post("/route-ticket", {
    message: message,
  });
};

// Get all saved tickets (admin only)
export const getTickets = () => {
  return API.get("/tickets");
};

// Get dashboard analytics (admin only)
export const getTicketStats = () => {
  return API.get("/tickets/stats");
};

// Get the logged-in customer's own ticket history
export const getMyTickets = () => {
  return API.get("/tickets/mine");
};

//This file is responsible for communicating with your FastAPI backend.
//If your backend URL changes later, you only update the .env file.
