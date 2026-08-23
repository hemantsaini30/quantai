// FILE LOCATION: quantai/apps/api/src/app.js
require("dotenv").config();

const express = require("express");
const cors = require("cors");
const healthRoutes = require("./shared/healthRoutes");

const app = express();

app.use(cors());
app.use(express.json());

// Phase 0: only the health-check route exists.
// Future phases register their own module routers here, e.g.:
//   const authRoutes = require("./modules/auth/authRoutes");
//   app.use("/api/auth", authRoutes);
app.use("/api/health", healthRoutes);

// Centralized error handler (kept minimal for Phase 0, extended later)
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
