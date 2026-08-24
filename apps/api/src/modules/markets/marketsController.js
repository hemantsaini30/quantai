// FILE LOCATION: quantai/apps/api/src/modules/markets/marketsController.js
const marketsService = require("./marketsService");

async function overview(req, res, next) {
  try {
    const market = req.query.market || "IN";
    const data = await marketsService.getOverview(market);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function indices(req, res, next) {
  try {
    const market = req.query.market || "IN";
    const data = await marketsService.getIndices(market);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function gainers(req, res, next) {
  try {
    const market = req.query.market || "IN";
    const limit = req.query.limit || 5;
    const data = await marketsService.getGainers(market, limit);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function losers(req, res, next) {
  try {
    const market = req.query.market || "IN";
    const limit = req.query.limit || 5;
    const data = await marketsService.getLosers(market, limit);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function mostActive(req, res, next) {
  try {
    const market = req.query.market || "IN";
    const limit = req.query.limit || 5;
    const data = await marketsService.getMostActive(market, limit);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function sectors(req, res, next) {
  try {
    const market = req.query.market || "IN";
    const data = await marketsService.getSectors(market);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function quote(req, res, next) {
  try {
    const data = await marketsService.getQuote(req.params.symbol);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function history(req, res, next) {
  try {
    const period = req.query.period || "3mo";
    const data = await marketsService.getHistory(req.params.symbol, period);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

async function search(req, res, next) {
  try {
    const market = req.query.market || "IN";
    const data = await marketsService.search(req.query.q, market);
    res.json(data);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  overview,
  indices,
  gainers,
  losers,
  mostActive,
  sectors,
  quote,
  history,
  search,
};