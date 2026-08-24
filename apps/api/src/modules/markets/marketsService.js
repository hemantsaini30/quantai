// FILE LOCATION: quantai/apps/api/src/modules/markets/marketsService.js
const axios = require("axios");
const redis = require("../../shared/redisClient");

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000";
const CACHE_TTL_SECONDS = 60; // market data is cached briefly, not fetched from
// yfinance on every single page load. 60s balances freshness against
// hammering Yahoo Finance with requests (which can trigger rate limiting —
// seen live during Section 2 testing).

async function cachedGet(cacheKey, fetchFn) {
  try {
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);
  } catch (err) {
    // Redis being briefly unavailable shouldn't break the feature — fall
    // through to a live fetch instead of failing the request.
    console.error("Redis cache read failed:", err.message);
  }

  const data = await fetchFn();

  try {
    await redis.set(cacheKey, JSON.stringify(data), "EX", CACHE_TTL_SECONDS);
  } catch (err) {
    console.error("Redis cache write failed:", err.message);
  }

  return data;
}

function translateError(err) {
  if (err.response && err.response.status === 400) {
    const error = new Error(err.response.data?.detail || "Invalid request");
    error.statusCode = 400;
    throw error;
  }
  const error = new Error("Market data service unavailable");
  error.statusCode = 503;
  throw error;
}

async function getOverview(market) {
  return cachedGet(`markets:overview:${market}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/overview`, {
        params: { market },
      });
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function getIndices(market) {
  return cachedGet(`markets:indices:${market}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/indices`, {
        params: { market },
      });
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function getGainers(market, limit) {
  return cachedGet(`markets:gainers:${market}:${limit}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/gainers`, {
        params: { market, limit },
      });
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function getLosers(market, limit) {
  return cachedGet(`markets:losers:${market}:${limit}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/losers`, {
        params: { market, limit },
      });
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function getMostActive(market, limit) {
  return cachedGet(`markets:most-active:${market}:${limit}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/most-active`, {
        params: { market, limit },
      });
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function getSectors(market) {
  return cachedGet(`markets:sectors:${market}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/sectors`, {
        params: { market },
      });
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function getQuote(symbol) {
  return cachedGet(`markets:quote:${symbol}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/quote/${symbol}`);
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function getHistory(symbol, period) {
  return cachedGet(`markets:history:${symbol}:${period}`, async () => {
    try {
      const res = await axios.get(`${AI_SERVICE_URL}/api/markets/history/${symbol}`, {
        params: { period },
      });
      return res.data;
    } catch (err) {
      translateError(err);
    }
  });
}

async function search(query, market) {
  // Search results are not cached — cheap operation on a small in-memory
  // list on the ai-service side, and caching every distinct query string
  // isn't worth the Redis memory.
  try {
    const res = await axios.get(`${AI_SERVICE_URL}/api/markets/search`, {
      params: { q: query, market },
    });
    return res.data;
  } catch (err) {
    translateError(err);
  }
}

module.exports = {
  getOverview,
  getIndices,
  getGainers,
  getLosers,
  getMostActive,
  getSectors,
  getQuote,
  getHistory,
  search,
};