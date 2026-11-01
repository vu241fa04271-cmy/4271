import axios from "axios";

// When VITE_API_URL is empty (dev proxy), calls go to /api/* and Vite forwards
// them to the Flask backend. In a production build, set VITE_API_URL to the
// backend origin (see .env.example).
const baseURL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Attach the JWT token to every request if one is stored.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize errors and auto-clear the token on auth failure.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const serverMessage =
      error.response?.data?.error || error.response?.data?.message;

    if (status === 401 && !error.config?.url?.includes("/auth/")) {
      // Token invalid/expired: clear it so the user is sent to login.
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }

    const normalized = new Error(serverMessage || error.message || "Request failed");
    normalized.status = status;
    normalized.original = error;
    return Promise.reject(normalized);
  }
);

export default api;
