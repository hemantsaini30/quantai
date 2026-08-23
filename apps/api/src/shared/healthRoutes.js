// FILE LOCATION: quantai/apps/api/src/shared/healthRoutes.js
const express = require("express");
const axios = require("axios");
const prisma = require("./prismaClient");
const redis = require("./redisClient");

const router = express.Router();

// GET /api/health
// Phase 0 definition of done: this single endpoint proves that
// api -> Postgres, api -> Redis, and api -> ai-service are all alive.
router.get("/", async (req, res) => {
  const result = {
    api: "ok",
    postgres: "unknown",
    redis: "unknown",
    aiService: "unknown",
  };

  try {
    await prisma.$queryRaw`SELECT 1`;
    result.postgres = "ok";
  } catch (err) {
    result.postgres = `error: ${err.message}`;
  }

  try {
    await redis.ping();
    result.redis = "ok";
  } catch (err) {
    result.redis = `error: ${err.message}`;
  }

  try {
    const aiServiceUrl = process.env.AI_SERVICE_URL || "http://localhost:8000";
    const response = await axios.get(`${aiServiceUrl}/health`, { timeout: 3000 });
    result.aiService = response.data?.status || "ok";
  } catch (err) {
    result.aiService = `error: ${err.message}`;
  }

  res.json(result);
});

module.exports = router;
