// Import axios library
import axios from "axios";

// Backend API URL (set in .env as VITE_API_URL, falls back to local dev)
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
});

// Route a support ticket
export const routeTicket = (message) => {
  return API.post("/route-ticket", {
    message: message,
  });
};

// Get all saved tickets
export const getTickets = () => {
  return API.get("/tickets");
};

// Get dashboard analytics (totals by priority/category/sentiment)
export const getTicketStats = () => {
  return API.get("/tickets/stats");
};

//This file is responsible for communicating with your FastAPI backend.
//If your backend URL changes later, you only update the .env file.
