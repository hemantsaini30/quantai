<!-- FILE LOCATION: quantai/docs/architecture/phase-plan.md -->

# QuantAI V2 — Phase Plan

Each phase produces a **working, demoable slice** — backend, API, frontend, tests, docs, and a git commit — before moving to the next. No phase starts backend work for the *next* phase early. This is the discipline V1 broke (big backend first, frontend postponed) and V2 is explicitly fixing.

---

## Phase 0 — Project Foundation
**Goal:** empty but fully wired skeleton. Nothing user-facing yet, but every piece of infrastructure exists and talks to every other piece.

- Monorepo scaffold: `apps/web`, `apps/api`, `apps/ai-service`, `packages/shared-types`, `packages/design-tokens`, `docs/`, `.github/workflows/`
- Postgres running (local via Docker Compose) + `pgvector` extension enabled
- Redis running (Docker Compose)
- Prisma initialized on `apps/api`, connected to Postgres
- Base FastAPI app in `apps/ai-service` with async DB session (SQLAlchemy/asyncpg) pointed at the same Postgres
- Base Vite+React app in `apps/web` with routing skeleton and the ink/paper/brass design tokens carried over from V1
- `apps/api` ↔ `apps/ai-service` proxy pattern re-established (health-check endpoint round trip: web → api → ai-service → back)
- CI: lint + build for all three apps on push (tests come with real code in Phase 1+)
- `docs/decisions/` started — first ADR: "why Postgres+pgvector over Mongo/separate vector DB" (already justified in the architecture doc, just formalized)

**Definition of done:** `docker compose up`, hit a `/health` endpoint in the browser, see a response that proves all three apps and both datastores are alive.

---

## Phase 1 — Public Market Dashboard
**Goal:** the homepage is useful with zero login, matching V2's stated #1 improvement over V1.

- **DB:** `assets`, `price_history` tables live; a script to backfill `price_history` from yfinance for a starter list of NIFTY/SENSEX constituents
- **ai-service:** market-data fetch/cache logic (carried over from V1's `marketDataService` pattern), endpoints for indices, top gainers/losers, most active, sector performance
- **api:** thin proxy module `modules/markets/`, with response caching via Redis (market data doesn't need to hit yfinance on every request)
- **web:** `features/markets/` — homepage with indices, an interactive price chart component, gainers/losers tables, sector performance view, basic stock search
- **Tests:** unit tests for market-data transforms; mocked service tests for the api↔ai-service boundary
- **Docs:** API doc for the markets endpoints; update architecture doc if the caching approach changes anything

**Definition of done:** a logged-out visitor sees live market data and can search/explore stocks.

---

## Phase 2 — Authentication
**Goal:** real accounts, protected routes, session handling — the gate that unlocks personalized features.

- **DB:** `users`, `refresh_tokens`
- **api:** `modules/auth/` — register, login, logout, JWT + refresh token rotation, password hashing, protected-route middleware
- **web:** `features/auth/` — register/login forms, auth state (context or store), protected-route wrapper, user profile page, visual "locked" states on nav items that require login (per your V2 spec)
- **Tests:** auth flow tests (register → login → access protected route → refresh → logout), middleware tests
- **Docs:** auth flow diagram, environment variables for JWT secrets

**Definition of done:** a user can register, log in, see their profile, get denied a protected route while logged out, and get access once logged in.

---

## Phase 3 — Portfolio Management
**Goal:** real, persistent portfolios — fixing V1's biggest limitation (Optimize page had no saved portfolio to work from).

- **DB:** `portfolios`, `holdings`, `portfolio_constraints`, `portfolio_constraint_overrides`
- **api:** `modules/portfolios/` — CRUD for portfolios, add/remove holdings, set quantity or target weight, set constraints (global + per-asset/sector overrides)
- **web:** `features/portfolios/` — portfolio list, create/edit portfolio, holdings editor (search-and-add asset, set weight/quantity), constraints editor, portfolio overview page showing current value (computed from `holdings` × latest `price_history`)
- **Tests:** CRUD tests, holdings-validation tests (weights summing sanely, no duplicate assets per portfolio — already enforced by the `UNIQUE (portfolio_id, asset_id)` constraint, but test the API's error handling around it)
- **Docs:** data model doc for portfolios/holdings, note on quantity-vs-weight duality

**Definition of done:** a logged-in user creates a portfolio, adds real holdings, sees its current value and composition.

---

## Phase 4 — Portfolio Analytics
**Goal:** users understand their portfolio *before* touching optimization.

- **DB:** no new tables (reads `holdings` + `price_history`); optionally introduce `analytics_snapshots` only if you want historical tracking of these metrics over time — deferred unless you want it now
- **ai-service:** analytics engine — expected return, volatility, Sharpe ratio, correlation matrix, risk contribution per holding, drawdown, historical performance series, computed straight from a portfolio's actual holdings and `price_history`
- **api:** `modules/analytics/` — thin proxy, portfolio-scoped
- **web:** `features/analytics/` — metric cards, correlation matrix heatmap, asset allocation chart, risk-contribution chart, drawdown/performance chart, all using the design system's monospace-for-numbers convention from V1
- **Tests:** pure-math unit tests for each metric (no mocking needed, same philosophy as V1), mocked service tests for the boundary
- **Docs:** formulas used for each metric, so future-you (or the RAG assistant) can explain them accurately

**Definition of done:** opening a portfolio shows a full analytical picture with real charts, no optimization involved yet.

---

## Phase 5 — Optimization (Markowitz + Black-Litterman + Efficient Frontier)
**Goal:** the core optimization engine, this time built against real saved portfolios from day one (not free-typed symbols like V1).

- **DB:** `optimization_runs`
- **ai-service:** `quant/` module — Markowitz solver, Black-Litterman pipeline (carried over from V1, re-integrated against the new portfolio schema), efficient-frontier computation, results persisted to `optimization_runs`
- **api:** `modules/optimization/` — run optimization for a portfolio, fetch run history
- **web:** `features/optimization/` — rebuilt Optimize workbench, now pulling from saved portfolio holdings/constraints instead of typed symbols, weight visualization (V1's stacked bar, carried forward), per-asset detail table, efficient-frontier chart (a genuine V1 gap being closed), run history view
- **Tests:** carry forward and extend V1's optimization test suite; add tests confirming persisted runs round-trip correctly
- **Docs:** note explicitly that this reuses/extends V1's proven Black-Litterman + Markowitz math, only the storage/UI layer is new

**Definition of done:** a user optimizes one of their real portfolios, sees weights + efficient frontier, and can look back at previous runs.

---

## Phase 6 — Monte Carlo Simulation
**Goal:** full user-facing simulation experience with async job handling (the first phase that needs Redis/BullMQ for real).

- **DB:** `simulation_runs`
- **ai-service:** `simulation/` module — carry forward V1's GBM + bootstrap engines and stress scenarios verbatim (they're already tested and correct), wire into the async job queue
- **api:** `modules/simulation/` — enqueue job, return job ID, status/result endpoint
- **web:** `features/simulation/` — parameter selection (horizon, method, goal amount), run button with async status (polling or websocket), percentile distribution chart, probability-of-loss display, stress scenario cards
- **Tests:** carry forward V1's 22+10 Monte Carlo tests; add job-queue integration tests (enqueue → process → retrieve result)
- **Docs:** note the GBM-vs-bootstrap "honest disagreement" principle from V1, since it'll surface in the UI and needs explaining to users, not hiding

**Definition of done:** a user runs a Monte Carlo simulation on a real portfolio and sees results appear asynchronously without a blocked UI.

---

## Phase 7 — Walk-Forward Backtesting
**Goal:** full backtesting interface, also async, comparing strategies over real history.

- **DB:** `backtest_runs`
- **ai-service:** `backtest/` module — carry forward V1's walk-forward engine (already correctly avoids lookahead bias, uses lookback expected returns per the locked-in V1 decision), wire into async queue
- **api:** `modules/backtest/` — enqueue, status, result, history endpoints
- **web:** `features/backtest/` — period/rebalance-frequency selection, async run status, equity curve chart (optimized vs equal-weight vs buy-and-hold), CAGR/vol/Sharpe/max-drawdown comparison table
- **Tests:** carry forward V1's 14 backtest tests plus its two regression tests (frozen-flat-period bug, self-referential-equilibrium bug); add job-queue tests
- **Docs:** document the "backtest only tests the optimization layer, not full LSTM+BL pipeline" scope decision from V1, since it'll be a natural question once users see it live

**Definition of done:** a user backtests a real portfolio's strategy against history and sees an honest, non-overstated comparison.

---

## Phase 8 — Advanced Risk Models (CVaR, Risk Parity, Risk Intelligence)
**Goal:** answer "where can this portfolio fail," not just "how much can it return."

- **DB:** no new tables — extends `optimization_runs.method` enum; risk-intelligence views likely reuse Phase 4's analytics patterns
- **ai-service:** CVaR optimization, Risk Parity optimization, concentration analysis, sector exposure analysis, deeper stress/scenario testing beyond V1's two hardcoded scenarios
- **api:** extends `modules/optimization/` and `modules/analytics/` rather than new modules
- **web:** new optimization method options in the existing Optimize workbench; risk-intelligence dashboard (concentration, sector exposure, scenario library)
- **Tests:** new solver tests (pure-math), scenario-analysis tests
- **Docs:** methodology notes for CVaR/Risk Parity, since these are more complex to explain than Markowitz and the RAG assistant (next phase) will need good source material

**Definition of done:** a user can optimize with CVaR/Risk Parity and see a genuine risk-focused view of their portfolio, not just return-focused.

---

## Phase 9 — RAG Infrastructure
**Goal:** the knowledge base and retrieval pipeline exist and work, before any chat UI sits on top of them.

- **DB:** `documents`, `document_chunks` (pgvector)
- **ai-service:** `rag/` module — ingestion pipeline (chunking, embedding via local `all-MiniLM-L6-v2`), retrieval function enforcing the `owner_scope` boundary, starting with **curated content only** (per the earlier decision) — financial glossary, methodology explanations, general research docs you write/curate yourself
- **api:** admin-only endpoint(s) to ingest curated documents (no user-upload yet — that's explicitly deferred)
- **web:** none required yet, or a minimal internal admin page to trigger ingestion — the RAG payoff is felt in Phase 10, not here
- **Tests:** chunking correctness, retrieval relevance sanity checks, `owner_scope` filter tests (critical — this is the access-boundary enforcement point)
- **Docs:** ADR on the embedding model choice and why local/free was chosen over a paid API

**Definition of done:** given a query, the retrieval function returns relevant chunks from curated documents, correctly scoped.

---

## Phase 10 — AI Financial Assistant
**Goal:** the actual differentiating feature — natural-language Q&A backed by RAG + tool-calling into QuantAI's own analytics, not just JSON-to-prose narration like V1.

- **DB:** `assistant_conversations`, `assistant_messages`
- **ai-service:** `ai/` module — LLM orchestration (still Groq, free tier, consistent with V1) with tool-calling into the optimization/analytics/simulation/backtest modules, RAG retrieval woven into the prompt, guardrails preserved and strengthened from V1 (never invent numbers, never give investment advice, and now also: clearly separate "retrieved fact" from "calculated result" in every answer, populate `cited_chunk_ids`)
- **api:** `modules/assistant/` — conversation CRUD, message send/receive
- **web:** `features/assistant/` — chat UI, portfolio-context switcher (general research chat vs. a specific portfolio's chat), source citations rendered under answers referencing retrieved chunks
- **Tests:** guardrail tests (does it refuse to invent a number when asked something outside its tool/retrieval reach?), tool-calling integration tests, citation-population tests
- **Docs:** the V1→V2 RAG architecture diagram from your planning doc, formalized as a real doc; explicit guardrail spec

**Definition of done:** a user asks "why did TCS get a higher allocation" or "explain my Monte Carlo result" in plain language and gets a grounded, cited, non-fabricated answer.

---

## Phase 11 — User Document Uploads (RAG extension)
**Goal:** extend Phase 9's RAG pipeline to user-owned documents, now that the curated pipeline and access-scoping are proven.

- **DB:** no schema change — `documents.owner_scope = 'user:<id>'` path already designed in Phase 9
- **ai-service:** upload handling, parsing (PDF/text), chunking reuse from Phase 9, ingestion into the same `document_chunks` table
- **api:** `modules/assistant/` (or a new `documents` sub-module) — upload endpoint, list/delete user documents
- **web:** document upload UI inside the assistant feature, list of a user's uploaded documents
- **Tests:** re-run and extend the `owner_scope` isolation tests from Phase 9 specifically against user uploads (this is the highest-risk area for a data leak between users)
- **Docs:** update the RAG ADR with the upload flow

**Definition of done:** a user uploads a research document and can ask the assistant questions about it, with zero chance another user's session sees it.

---

## Phase 12 — Rebalancing Recommendations
**Goal:** close the loop — from "here's your optimal allocation" to "here's what to actually trade to get there."

- **DB:** likely a new `rebalancing_recommendations` table (portfolio_id, from current holdings, to target weights from a chosen `optimization_run`, suggested trades) — small addition, additive to existing schema
- **ai-service:** diff current holdings vs. a target optimization run, produce buy/sell suggestions (quantity or weight delta), respecting constraints
- **api:** `modules/portfolios/` extension or new `modules/rebalancing/`
- **web:** rebalancing view attached to a portfolio, showing suggested trades against a chosen optimization run
- **Tests:** diff-logic tests, constraint-respecting tests
- **Docs:** clarify this produces *suggestions*, not executed trades — no brokerage integration in scope

**Definition of done:** a user picks a past optimization run and sees concrete suggested trades to move their current portfolio toward it.

---

## Phase 13 — Polish, Testing, Deployment
**Goal:** production readiness across the whole product, not a new feature.

- Full regression pass across all phases; fill any test gaps
- Loading/error/empty states audited across every feature (per V2's frontend-as-first-class-product requirement)
- Performance pass: query indexes, Redis cache hit rates, ai-service memory footprint (V1's known concern re: torch/transformers on free-tier hosting)
- CI/CD: full pipeline (test → build → deploy) for all three apps
- Deployment: choose hosting (carry the V1 discussion forward — Render or similar, now accounting for Postgres+pgvector+Redis instead of just Mongo)
- Final documentation pass: architecture doc, API docs, ADRs, README, environment setup guide
- Docker Compose finalized to cover the full stack (V1 only covered Mongo+gateway — V2 needs Postgres, Redis, api, ai-service, web)

**Definition of done:** a fresh clone + documented setup steps gets a new contributor to a fully running local stack, and the product is live at a deployed URL.

---

## Summary table

| Phase | Feature | New DB tables |
|---|---|---|
| 0 | Project foundation | — |
| 1 | Public market dashboard | `assets`, `price_history` |
| 2 | Authentication | `users`, `refresh_tokens` |
| 3 | Portfolio management | `portfolios`, `holdings`, `portfolio_constraints`, `portfolio_constraint_overrides` |
| 4 | Portfolio analytics | — (reads existing tables) |
| 5 | Optimization + efficient frontier | `optimization_runs` |
| 6 | Monte Carlo | `simulation_runs` |
| 7 | Backtesting | `backtest_runs` |
| 8 | Advanced risk models | — (extends existing) |
| 9 | RAG infrastructure | `documents`, `document_chunks` |
| 10 | AI financial assistant | `assistant_conversations`, `assistant_messages` |
| 11 | User document uploads | — (extends Phase 9 tables) |
| 12 | Rebalancing recommendations | `rebalancing_recommendations` |
| 13 | Polish, testing, deployment | — |

Each phase ends in a git commit (or small set of commits) following the `feat(module): description` convention from your engineering-discipline requirements, and each is independently demoable — you should be able to stop after any phase and have something real to show.
