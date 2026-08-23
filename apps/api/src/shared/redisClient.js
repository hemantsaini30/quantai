// FILE LOCATION: quantai/apps/api/src/shared/redisClient.js
const Redis = require("ioredis");

// Single shared Redis instance. Used for:
//  - caching (e.g. market data, Phase 1)
//  - BullMQ job queues (Monte Carlo / backtest, Phases 6-7)
const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379");

redis.on("error", (err) => {
  console.error("Redis connection error:", err.message);
});

module.exports = redis;
