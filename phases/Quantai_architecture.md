# QuantAI V2 — Architecture & Database Schema

## 1. Technology decisions

| Concern | Decision | Why |
|---|---|---|
| Primary database | **PostgreSQL** | Portfolios/holdings/backtests/RAG docs are inherently relational (FKs, joins, transactional consistency). Mongo's schema-less model was a liability once V1 grew past module 1-2. |
| Vector search (RAG) | **pgvector extension on the same Postgres instance** | Avoids a second database/ops surface. Vector search can be joined directly against user/portfolio tables in SQL. Migrate to a dedicated vector DB later only if scale demands it — isolated migration, not a rewrite. |
| Cache / job queue | **Redis** | Already flagged as a known gap in V1 (async job queue for long-running Monte Carlo/backtest runs). Redis + BullMQ (Node) for job queuing, plus general caching (market data, computed analytics). |
| ORM | **Prisma** (Node gateway) — schema-first, generates types shared conceptually with frontend | Matches "feature-module" organization goal; migrations are explicit and reviewable in git history, satisfying the engineering-discipline requirement. |
| Python side DB access | **SQLAlchemy (async) or asyncpg**, reading the same Postgres | ai-service needs read access to portfolios/holdings for optimization/backtest; avoid a second source of truth. |

---

## 2. Monorepo layout

```
quantai/
├── apps/
│   ├── web/                        # React + Vite + Tailwind
│   │   └── src/
│   │       ├── features/           # feature-module organization, NOT global pages/ or components/
│   │       │   ├── markets/
│   │       │   ├── auth/
│   │       │   ├── portfolios/
│   │       │   ├── analytics/
│   │       │   ├── optimization/
│   │       │   ├── simulation/
│   │       │   ├── backtest/
│   │       │   └── assistant/      # RAG chat UI
│   │       ├── shared/             # design system, api client, hooks
│   │       └── app/                # routing, providers, App.jsx
│   │
│   ├── api/                        # Node/Express gateway (renamed from "gateway")
│   │   └── src/
│   │       ├── modules/
│   │       │   ├── auth/           # controller+service+routes+schema per module
│   │       │   ├── markets/
│   │       │   ├── portfolios/
│   │       │   ├── analytics/
│   │       │   ├── optimization/
│   │       │   ├── simulation/
│   │       │   ├── backtest/
│   │       │   └── assistant/
│   │       ├── shared/             # db client, error middleware, auth middleware
│   │       └── app.js
│   │
│   └── ai-service/                 # Python/FastAPI
│       └── app/
│           ├── api/                # routers only, thin
│           ├── quant/              # Markowitz, Black-Litterman, efficient frontier, CVaR, risk parity
│           ├── ml/                 # LSTM, XGBoost, FinBERT
│           ├── simulation/         # Monte Carlo engines
│           ├── backtest/           # walk-forward engine
│           ├── rag/                # ingestion, chunking, embedding, retrieval
│           ├── ai/                 # LLM orchestration, tool-calling, guardrails
│           └── core/               # config, db session, logging
│
├── packages/
│   ├── shared-types/                # TypeScript types shared between web and api (portfolio, holding, etc.)
│   └── design-tokens/                # ink/paper/brass palette, carried forward from V1
│
├── docs/
│   ├── architecture/
│   ├── api/                          # OpenAPI specs, endpoint docs
│   └── decisions/                    # ADRs — one file per major decision, mirrors V1's "locked-in conventions" habit
│
└── .github/
    └── workflows/                    # CI: lint, test, build per app
```

**Rationale for `apps/web` and `apps/api` renames (from V1's `frontend`/`gateway`):** purely cosmetic clarity, optional — keep V1 names if you'd rather avoid the churn. The structural change that matters is *feature-module folders instead of global `pages/`, `services/`, `controllers/`, `routes/`*. V1 already showed the pain of this: adding Optimize touched 6 different global folders across 2 apps. A feature module keeps everything for "optimization" in one place across the stack boundary it can control (its own controller/service/route on the API side).

---

## 3. Service boundaries

- **web** never talks to **ai-service** directly. All requests go through **api**, which is the only service holding the JWT/session logic and the only service with a DB connection pool sized for user-facing traffic.
- **api** is a thin proxy + auth/validation layer for anything quantitative (mirrors V1's proven pattern), but *owns* auth, portfolios, and market-data caching directly (no need to round-trip to Python for simple CRUD).
- **ai-service** owns everything CPU/ML-heavy: optimization, simulation, backtesting, RAG retrieval, and LLM orchestration. It reads from the same Postgres (read-heavy: portfolio/holdings/price data) and writes results back (optimization runs, simulation runs, backtest runs) rather than being stateless — this is what makes "show me my last 5 backtests" possible without recomputation.
- **Redis** sits between api and ai-service for long-running jobs: api enqueues a job, returns a job ID immediately, frontend polls or uses a websocket for status. This directly fixes the V1 known-issue of no async job queue.
  - **Scope, deliberately narrow**: only **Monte Carlo** and **backtest** runs go through the async queue. Both involve either thousands of simulated paths or many chained optimization solves across rebalance dates, and are the only operations where a blocking HTTP request becomes a real UX problem.
  - **Optimization (Markowitz/Black-Litterman/CVaR/Risk Parity) stays synchronous** — a single CVXPY solve is sub-second, and adding job-ID/polling machinery there would be complexity with no payoff. If a future optimization method turns out to be slow, it can be moved onto the same async path without affecting the others.

---

## 4. Database schema

Conventions: `uuid` primary keys throughout (avoids leaking sequential IDs, works cleanly across services). `created_at`/`updated_at` on every table (omitted below for brevity except where meaningfully different). Money/weight values use `numeric`, never `float`.

### 4.1 Users & Auth

```sql
users (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email             text UNIQUE NOT NULL,
  password_hash     text NOT NULL,
  display_name      text,
  role              text NOT NULL DEFAULT 'user',   -- 'user' | 'admin'
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

refresh_tokens (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash        text NOT NULL,
  expires_at        timestamptz NOT NULL,
  revoked_at        timestamptz
);
```

### 4.2 Assets & Market Data

```sql
assets (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol            text UNIQUE NOT NULL,        -- 'TCS.NS'
  name              text NOT NULL,
  exchange          text,
  sector            text,
  asset_type        text NOT NULL DEFAULT 'equity',
  currency          text NOT NULL DEFAULT 'INR'
);

-- Daily OHLCV cache, populated from yfinance, avoids re-fetching on every request
price_history (
  asset_id          uuid NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  date              date NOT NULL,
  open              numeric,
  high              numeric,
  low               numeric,
  close             numeric NOT NULL,
  volume            bigint,
  PRIMARY KEY (asset_id, date)
);
```

### 4.3 Portfolios & Holdings

```sql
portfolios (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name              text NOT NULL,
  base_currency     text NOT NULL DEFAULT 'INR',
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

-- Current state, not transaction history (see decision above).
-- Designed so a future `transactions` table can populate this via
-- a recompute job, rather than replacing this table's shape.
holdings (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id      uuid NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asset_id          uuid NOT NULL REFERENCES assets(id),
  quantity          numeric,             -- nullable: user may specify weight instead
  target_weight     numeric,             -- nullable: user may specify quantity instead
  UNIQUE (portfolio_id, asset_id)
);

-- Global defaults for the portfolio. Per-asset/per-sector overrides live in
-- portfolio_constraint_overrides below, kept separate so the common case
-- (just global max/min) stays simple, while CVaR/Risk Parity can layer
-- asset-class-level bounds later without migrating this table.
portfolio_constraints (
  portfolio_id      uuid PRIMARY KEY REFERENCES portfolios(id) ON DELETE CASCADE,
  max_weight_per_asset   numeric,
  min_weight_per_asset   numeric,
  max_sector_weight      numeric,
  allow_short            boolean NOT NULL DEFAULT false
);

portfolio_constraint_overrides (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id      uuid NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  scope_type        text NOT NULL,        -- 'asset' | 'sector'
  scope_ref         text NOT NULL,        -- asset_id (as text) or sector name, depending on scope_type
  max_weight        numeric,
  min_weight        numeric,
  UNIQUE (portfolio_id, scope_type, scope_ref)
);
```

### 4.4 Analytical Runs (Optimization, Simulation, Backtest)

Each of these is a **stored run**, not a stateless calculation — this is what lets the frontend show history ("your last 3 optimizations") without recomputation, and is what the AI assistant/RAG layer will cite against ("your latest Monte Carlo run showed...").

```sql
optimization_runs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id      uuid NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  method            text NOT NULL,        -- 'markowitz' | 'black_litterman' | 'cvar' | 'risk_parity'
  input_params      jsonb NOT NULL,       -- constraints, target return, etc. at time of run
  result_weights    jsonb NOT NULL,       -- {asset_id: weight}
  expected_return   numeric,
  expected_volatility numeric,
  sharpe_ratio      numeric,
  created_at        timestamptz NOT NULL DEFAULT now()
);

simulation_runs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id      uuid NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  method            text NOT NULL,        -- 'gbm' | 'bootstrap' | 'both'
  input_params      jsonb NOT NULL,       -- horizon, num_paths, goal amount, etc.
  result_summary    jsonb NOT NULL,       -- percentiles, prob_of_loss, stress scenarios
  created_at        timestamptz NOT NULL DEFAULT now()
);

backtest_runs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id      uuid NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  start_date        date NOT NULL,
  end_date          date NOT NULL,
  rebalance_freq    text NOT NULL,        -- 'monthly' | 'quarterly' | 'annually'
  result_metrics    jsonb NOT NULL,       -- CAGR/vol/Sharpe/max_dd per strategy
  equity_curve      jsonb NOT NULL,       -- time series per strategy, for charting
  created_at        timestamptz NOT NULL DEFAULT now()
);
```

*(`jsonb` is used deliberately here, not as a schema cop-out — these are heterogeneous, versioned result blobs where the shape legitimately varies by method, and they're written once/read-mostly, which is exactly jsonb's good case in Postgres. The strongly-typed relational tables are for entities with real relationships: users, portfolios, holdings, assets.)*

### 4.5 RAG — Knowledge Base

```sql
-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

documents (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_scope       text NOT NULL,        -- 'global' | 'user:<uuid>' — enforces the access boundary at the schema level
  title             text NOT NULL,
  source_type       text NOT NULL,        -- 'curated' | 'user_upload'
  source_uri        text,                 -- original file path/URL if applicable
  created_at        timestamptz NOT NULL DEFAULT now()
);

document_chunks (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id       uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index       int NOT NULL,
  content           text NOT NULL,
  embedding         vector(384),          -- sentence-transformers/all-MiniLM-L6-v2, run locally in ai-service (keeps the "no paid APIs" principle from V1 — no OpenAI embedding calls)
  UNIQUE (document_id, chunk_index)
);

CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

**On `owner_scope`:** retrieval queries must always filter `owner_scope = 'global' OR owner_scope = 'user:' || :current_user_id`. This is the mechanism that keeps one user's uploaded document from ever appearing in another user's RAG context — worth enforcing as a single shared query helper in `ai-service/app/rag/`, not re-implemented per endpoint.

### 4.6 AI Assistant Conversations

```sql
assistant_conversations (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  portfolio_id      uuid REFERENCES portfolios(id),   -- nullable: general research chat vs portfolio-specific
  created_at        timestamptz NOT NULL DEFAULT now()
);

assistant_messages (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id   uuid NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
  role              text NOT NULL,         -- 'user' | 'assistant' | 'tool'
  content           text NOT NULL,
  tool_calls        jsonb,                 -- which QuantAI tools were invoked, for auditability/debugging
  cited_chunk_ids   uuid[],                -- traceability: which document_chunks backed this answer
  created_at        timestamptz NOT NULL DEFAULT now()
);
```

`cited_chunk_ids` directly supports the V2 requirement to "distinguish retrieved facts from model calculations" and "cite retrieved information where appropriate" — it's cheap to store and is what will let the frontend render "sources" under an assistant answer.

---

## 5. How this maps to the V2 build order

| Build step | Tables touched |
|---|---|
| 2. Public Market Dashboard | `assets`, `price_history` |
| 3. Authentication | `users`, `refresh_tokens` |
| 4. Portfolio Management | `portfolios`, `holdings`, `portfolio_constraints` |
| 5. Portfolio Analytics | reads `holdings` + `price_history`, no new tables (analytics are computed, not stored, unless you want history — can add `analytics_snapshots` later following the same pattern as `optimization_runs`) |
| 6-7. Markowitz/BL/Efficient Frontier | `optimization_runs` |
| 8. Monte Carlo | `simulation_runs` |
| 9. Backtesting | `backtest_runs` |
| 10. Advanced Risk Models | extends `optimization_runs.method` enum, no schema change |
| 11. RAG Infrastructure | `documents`, `document_chunks` |
| 12. AI Financial Assistant | `assistant_conversations`, `assistant_messages` |

This ordering means every step's schema is additive — nothing built early needs to be reshaped by something built later, which matters given the "every feature end-to-end, then commit" discipline you've set for V2.

---

## 6. Decisions locked in (resolving the open questions above)

1. **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim), run locally inside `ai-service`. No paid embedding API — consistent with V1's yfinance/Groq-free-tier principle, and avoids per-document billing as the knowledge base grows. Schema uses `vector(384)`.
2. **Job queue scope**: Redis/BullMQ used only for **Monte Carlo** and **backtest** runs. Optimization (Markowitz/Black-Litterman/CVaR/Risk Parity) stays synchronous — sub-second CVXPY solves don't justify job-ID/polling complexity. Revisit per-method only if a specific optimization variant proves slow in practice.
3. **Constraint overrides**: added as a separate `portfolio_constraint_overrides` table (scope_type: `asset` | `sector`) rather than columns on `portfolio_constraints`. Keeps the common case (global max/min only) simple while giving CVaR/Risk Parity room for per-asset or per-sector bounds without a later migration.