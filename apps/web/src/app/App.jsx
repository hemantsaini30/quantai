// FILE LOCATION: quantai/apps/web/src/app/App.jsx
import { Routes, Route } from "react-router-dom";
import HealthCheckPage from "../features/health/HealthCheckPage";

// Future phases add their feature routes here, e.g.:
// import MarketsHome from "../features/markets/MarketsHome";
// <Route path="/" element={<MarketsHome />} />

function App() {
  return (
    <Routes>
      <Route path="/" element={<HealthCheckPage />} />
    </Routes>
  );
}

export default App;
