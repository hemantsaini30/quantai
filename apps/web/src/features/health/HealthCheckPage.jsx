// FILE LOCATION: quantai/apps/web/src/features/health/HealthCheckPage.jsx
import { useEffect, useState } from "react";
import apiClient from "../../shared/apiClient";

// Phase 0 definition of done: this page proves that
// web -> api -> Postgres, api -> Redis, and api -> ai-service -> Postgres
// are all connected and alive. Delete or replace once Phase 1's
// MarketsHome page exists as the real "/" route.
function HealthCheckPage() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiClient
      .get("/health")
      .then((res) => setStatus(res.data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white border border-slate/20 rounded-lg p-8 max-w-md w-full">
        <h1 className="font-serif text-2xl text-ink mb-4">QuantAI — Phase 0</h1>
        <p className="text-slate mb-6">System health check</p>

        {error && <p className="text-risk font-mono text-sm">{error}</p>}

        {status && (
          <ul className="space-y-2 font-mono text-sm">
            <li>api: <span className="text-gain">{status.api}</span></li>
            <li>postgres: <span className={status.postgres === "ok" ? "text-gain" : "text-risk"}>{status.postgres}</span></li>
            <li>redis: <span className={status.redis === "ok" ? "text-gain" : "text-risk"}>{status.redis}</span></li>
            <li>aiService: <span className={status.aiService === "ok" ? "text-gain" : "text-risk"}>{status.aiService}</span></li>
          </ul>
        )}

        {!status && !error && <p className="text-slate font-mono text-sm">Checking...</p>}
      </div>
    </div>
  );
}

export default HealthCheckPage;
