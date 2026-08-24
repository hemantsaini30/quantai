// FILE LOCATION: quantai/apps/api/src/modules/markets/marketsRoutes.js
const express = require("express");
const controller = require("./marketsController");

const router = express.Router();

router.get("/overview", controller.overview);
router.get("/indices", controller.indices);
router.get("/gainers", controller.gainers);
router.get("/losers", controller.losers);
router.get("/most-active", controller.mostActive);
router.get("/sectors", controller.sectors);
router.get("/search", controller.search);
router.get("/quote/:symbol", controller.quote);
router.get("/history/:symbol", controller.history);

module.exports = router;