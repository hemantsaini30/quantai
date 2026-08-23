<!-- FILE LOCATION: quantai/docs/decisions/001-postgres-pgvector-over-mongo.md -->
# ADR 001: PostgreSQL + pgvector instead of MongoDB + separate vector DB

## Status
Accepted

## Context
V1 used MongoDB. V2 adds portfolios, holdings, optimization/simulation/backtest
run history, and a RAG knowledge base — all of which have real relational
structure (foreign keys, joins) rather than being naturally document-shaped.

## Decision
Use PostgreSQL as the single primary database for all of V2, with the
`pgvector` extension for RAG embedding storage/search, instead of:
- MongoDB (V1's choice), or
- Postgres + a separate dedicated vector database (Pinecone, Weaviate, Qdrant)

## Reasoning
- Portfolios -> holdings -> assets -> price_history, and optimization/simulation/
  backtest runs referencing portfolios, are genuinely relational. Modeling this
  in Mongo means either denormalizing everywhere or doing joins in application
  code.
- Financial figures benefit from Postgres's `numeric` type and strong typing,
  versus schema-less JSON documents.
- Keeping RAG vectors in the same Postgres instance (via pgvector) avoids a
  second database to operate, back up, and reason about. Vector search can be
  joined directly against portfolio/user tables in a single SQL query (e.g.
  "retrieve chunks visible to this user").
- If RAG scale ever demands a dedicated vector database, that migration is
  isolated (only the `documents`/`document_chunks` tables) rather than a
  rewrite of the whole data layer.

## Consequences
- apps/api uses Prisma against Postgres.
- apps/ai-service uses SQLAlchemy (async) against the same Postgres instance
  as apps/api — one source of truth, no data duplication.
- Local dev requires Postgres with the pgvector extension, provided via the
  `pgvector/pgvector:pg16` Docker image in docker-compose.yml.
