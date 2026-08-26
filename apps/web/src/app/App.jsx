// FILE LOCATION: quantai/apps/web/src/app/App.jsx
import { Routes, Route } from "react-router-dom";
import MarketDashboardPage from "../features/markets/MarketDashboardPage";
import HealthCheckPage from "../features/health/HealthCheckPage";

// Future phases add their feature routes here, e.g.:
// import LoginPage from "../features/auth/LoginPage";
// <Route path="/login" element={<LoginPage />} />

function App() {
  return (
    <Routes>
      <Route path="/" element={<MarketDashboardPage />} />
      <Route path="/health" element={<HealthCheckPage />} />
    </Routes>
  );
}

export default App;