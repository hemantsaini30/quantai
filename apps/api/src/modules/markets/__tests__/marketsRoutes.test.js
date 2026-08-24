// FILE LOCATION: quantai/apps/api/src/modules/markets/__tests__/marketsRoutes.test.js
// Supertest integration tests: real HTTP requests through a real Express
// app instance, with only the service layer mocked. This verifies routing,
// query/param parsing, status codes, and the error-handler middleware —
// none of which marketsService.test.js (Section 3) covers, since that
// tested the service function in isolation without Express involved.

jest.mock("../marketsService");
jest.mock("../../../shared/redisClient", () => ({
  get: jest.fn(),
  set: jest.fn(),
  quit: jest.fn(),
}));

const request = require("supertest");
const express = require("express");
const marketsService = require("../marketsService");
const marketsRoutes = require("../marketsRoutes");

function buildTestApp() {
  const app = express();
  app.use(express.json());
  app.use("/api/markets", marketsRoutes);
  // same minimal error handler shape as the real app.js
  app.use((err, req, res, next) => {
    res.status(err.statusCode || 500).json({ message: err.message || "Internal server error" });
  });
  return app;
}

describe("markets routes", () => {
  let app;
    afterAll(async () => {
    // Belt-and-suspenders: even with redisClient mocked above, this
    // ensures no real Redis connection is ever left open by this suite.
    const redis = require("../../../shared/redisClient");
    if (redis.quit) await redis.quit();
  });

  beforeEach(() => {
    jest.clearAllMocks();
    app = buildTestApp();
  });

  it("GET /api/markets/overview returns 200 with service data", async () => {
    marketsService.getOverview.mockResolvedValue({ indices: [], top_gainers: [] });

    const res = await request(app).get("/api/markets/overview?market=IN");

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ indices: [], top_gainers: [] });
    expect(marketsService.getOverview).toHaveBeenCalledWith("IN");
  });

  it("GET /api/markets/overview defaults market to IN when not provided", async () => {
    marketsService.getOverview.mockResolvedValue({});

    await request(app).get("/api/markets/overview");

    expect(marketsService.getOverview).toHaveBeenCalledWith("IN");
  });

  it("GET /api/markets/gainers passes market and limit through", async () => {
    marketsService.getGainers.mockResolvedValue([]);

    await request(app).get("/api/markets/gainers?market=US&limit=10");

    expect(marketsService.getGainers).toHaveBeenCalledWith("US", "10");
  });

  it("GET /api/markets/quote/:symbol passes the symbol from the URL path", async () => {
    marketsService.getQuote.mockResolvedValue({ symbol: "AAPL", last_price: 200 });

    const res = await request(app).get("/api/markets/quote/AAPL");

    expect(res.status).toBe(200);
    expect(res.body.symbol).toBe("AAPL");
    expect(marketsService.getQuote).toHaveBeenCalledWith("AAPL");
  });

  it("GET /api/markets/search passes q and market to the service", async () => {
    marketsService.search.mockResolvedValue([{ symbol: "TCS.NS" }]);

    const res = await request(app).get("/api/markets/search?q=tcs&market=IN");

    expect(res.status).toBe(200);
    expect(marketsService.search).toHaveBeenCalledWith("tcs", "IN");
  });

  it("returns the correct status code and message when the service throws a 503", async () => {
    const err = new Error("Market data service unavailable");
    err.statusCode = 503;
    marketsService.getOverview.mockRejectedValue(err);

    const res = await request(app).get("/api/markets/overview");

    expect(res.status).toBe(503);
    expect(res.body.message).toBe("Market data service unavailable");
  });

  it("returns 400 with the specific message when the service throws a 400", async () => {
    const err = new Error("Invalid market code");
    err.statusCode = 400;
    marketsService.getIndices.mockRejectedValue(err);

    const res = await request(app).get("/api/markets/indices?market=ZZ");

    expect(res.status).toBe(400);
    expect(res.body.message).toBe("Invalid market code");
  });
});