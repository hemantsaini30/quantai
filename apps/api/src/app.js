// FILE LOCATION: quantai/apps/api/src/app.js
require("dotenv").config();

const express = require("express");
const cors = require("cors");
const healthRoutes = require("./shared/healthRoutes");
const marketsRoutes = require("./modules/markets/marketsRoutes");

const app = express();

app.use(cors());
app.use(express.json());

app.use("/api/health", healthRoutes);
app.use("/api/markets", marketsRoutes);

// Future phases register their own module routers here, e.g.:
//   const authRoutes = require("./modules/auth/authRoutes");
//   app.use("/api/auth", authRoutes);

// Centralized error handler (kept minimal for Phase 0/1, extended later)
app.use((err, req, res, next) => {
  console.error(err);
  res.status(err.statusCode || 500).json({
    message: err.message || "Internal server error",
  });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`QuantAI API listening on port ${PORT}`);
});

module.exports = app;