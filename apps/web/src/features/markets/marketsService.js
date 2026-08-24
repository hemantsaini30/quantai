// FILE LOCATION: quantai/apps/web/src/features/markets/marketsService.js
import apiClient from "../../shared/apiClient";

// One function per backend endpoint, unwrapping res.data — matches the
// pattern locked in for all frontend service files.

export async function getOverview(market) {
  const res = await apiClient.get("/markets/overview", { params: { market } });
  return res.data;
}

export async function getGainers(market, limit = 5) {
  const res = await apiClient.get("/markets/gainers", { params: { market, limit } });
  return res.data;
}

export async function getLosers(market, limit = 5) {
  const res = await apiClient.get("/markets/losers", { params: { market, limit } });
  return res.data;
}

export async function getMostActive(market, limit = 5) {
  const res = await apiClient.get("/markets/most-active", { params: { market, limit } });
  return res.data;
}

export async function getSectors(market) {
  const res = await apiClient.get("/markets/sectors", { params: { market } });
  return res.data;
}

export async function getQuote(symbol) {
  const res = await apiClient.get(`/markets/quote/${symbol}`);
  return res.data;
}

export async function getHistory(symbol, period = "3mo") {
  const res = await apiClient.get(`/markets/history/${symbol}`, { params: { period } });
  return res.data;
}

export async function search(query, market) {
  const res = await apiClient.get("/markets/search", { params: { q: query, market } });
  return res.data;
}