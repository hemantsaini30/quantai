// FILE LOCATION: quantai/apps/api/src/shared/prismaClient.js
const { PrismaClient } = require("@prisma/client");

// Single shared Prisma instance, imported by every module's service file.
// Avoids exhausting the Postgres connection pool by creating a new client
// per module.
const prisma = new PrismaClient();

module.exports = prisma;
