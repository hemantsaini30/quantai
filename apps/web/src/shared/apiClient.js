// FILE LOCATION: quantai/apps/web/src/shared/apiClient.js
import axios from "axios";

// Single shared axios instance pointed at apps/api.
// Every feature's service file (e.g. features/markets/marketsService.js)
// should import this rather than creating its own axios instance.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:4000/api",
});

export default apiClient;
