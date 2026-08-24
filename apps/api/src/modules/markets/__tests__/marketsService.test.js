// FILE LOCATION: quantai/apps/api/src/modules/markets/__tests__/marketsService.test.js
jest.mock("axios");
jest.mock("../../../shared/redisClient", () => ({
  get: jest.fn(),
  set: jest.fn(),
}));

const axios = require("axios");
const redis = require("../../../shared/redisClient");
const marketsService = require("../marketsService");

describe("marketsService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("getOverview", () => {
    it("returns cached data without calling ai-service if cache hit", async () => {
      const cachedData = { indices: [], top_gainers: [] };
      redis.get.mockResolvedValue(JSON.stringify(cachedData));

      const result = await marketsService.getOverview("IN");

      expect(result).toEqual(cachedData);
      expect(axios.get).not.toHaveBeenCalled();
    });

    it("fetches from ai-service and caches on cache miss", async () => {
      redis.get.mockResolvedValue(null);
      const liveData = { indices: [{ symbol: "^NSEI" }] };
      axios.get.mockResolvedValue({ data: liveData });

      const result = await marketsService.getOverview("IN");

      expect(result).toEqual(liveData);
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining("/api/markets/overview"),
        expect.objectContaining({ params: { market: "IN" } })
      );
      expect(redis.set).toHaveBeenCalledWith(
        "markets:overview:IN",
        JSON.stringify(liveData),
        "EX",
        60
      );
    });

    it("falls back to a live fetch if redis read fails", async () => {
      redis.get.mockRejectedValue(new Error("redis down"));
      const liveData = { indices: [] };
      axios.get.mockResolvedValue({ data: liveData });

      const result = await marketsService.getOverview("IN");

      expect(result).toEqual(liveData);
    });

    it("translates a non-400 ai-service error into a 503", async () => {
      redis.get.mockResolvedValue(null);
      axios.get.mockRejectedValue(new Error("connection refused"));

      await expect(marketsService.getOverview("IN")).rejects.toMatchObject({
        statusCode: 503,
      });
    });

    it("translates a 400 ai-service error into a 400 with the detail message", async () => {
      redis.get.mockResolvedValue(null);
      const err = new Error("bad request");
      err.response = { status: 400, data: { detail: "Invalid market code" } };
      axios.get.mockRejectedValue(err);

      await expect(marketsService.getOverview("IN")).rejects.toMatchObject({
        statusCode: 400,
        message: "Invalid market code",
      });
    });
  });

  describe("search", () => {
    it("does not use the cache (search results are not cached)", async () => {
      axios.get.mockResolvedValue({ data: [{ symbol: "TCS.NS" }] });

      await marketsService.search("tcs", "IN");

      expect(redis.get).not.toHaveBeenCalled();
      expect(redis.set).not.toHaveBeenCalled();
    });
  });
});