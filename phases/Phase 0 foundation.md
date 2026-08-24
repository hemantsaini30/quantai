<!-- FILE LOCATION: quantai/docs/phases/phase-0-foundation.md -->
<!-- If the "phases" folder doesn't exist yet under docs/, just create it and drop this file in. -->

# Phase 0 — Project Foundation

## What this phase was about

Before building any real feature (market dashboard, portfolios, optimization, etc.), we set up the **skeleton** of the whole project — three separate apps that can talk to each other, two databases running locally, and proof that the full chain works end to end.

Nothing user-facing was built yet. This phase was purely: *"does the plumbing work?"*

---

## What we actually built

- A **monorepo** (one Git repository containing all three apps, instead of three separate repos)
- Three apps, empty except for a health-check:
  - `apps/web` — the website (what a user sees in the browser)
  - `apps/api` — the middleman server (handles logins, portfolios, talks to the database)
  - `apps/ai-service` — the Python brain (does the math/ML/AI work)
- Two databases running in Docker containers on your laptop
- A webpage that checks all four pieces (web, api, database, ai-service) and shows "ok" for each — this was our proof that everything is wired correctly

---

## New tools/technologies used — explained simply

### Docker / Docker Desktop
**What it is:** A way to run software (like a database) in an isolated "box" (called a *container*) without installing it directly onto your Windows system.

**Why we used it:** Instead of installing Postgres and Redis manually on Windows (which involves messy setup, PATH issues, version conflicts), Docker lets us start both with a single command: `docker compose up -d`. If something breaks, we delete the container and start fresh — nothing gets permanently messed up on your laptop.

**Analogy:** Think of it like a shipping container — the software and everything it needs to run is packed inside, and it runs the same way no matter what "ship" (computer) it's placed on.

---

### PostgreSQL (Postgres)
**What it is:** A database — a system for storing structured data permanently (users, portfolios, prices, etc.) so it survives even after you close the app.

**Why we chose it over MongoDB (used in V1):** Our data has real relationships — a portfolio *has* holdings, a holding *references* an asset, a backtest *belongs to* a portfolio. Postgres is built for exactly this kind of connected data (it's a "relational" database). MongoDB stores loose, flexible documents, which was fine for V1's early experiments but becomes awkward once you have many connected pieces.

---

### pgvector
**What it is:** An add-on (extension) for Postgres that lets it store and search "embeddings" — lists of numbers that represent the *meaning* of text, used for AI search features.

**Why we need it (later, not yet):** In Phase 9, we'll build a RAG (AI search) feature — "ask a question, get an answer based on relevant documents." That requires storing documents as embeddings and searching them by meaning, not just keywords. Setting this up now (via the `pgvector/pgvector:pg16` Docker image) means we don't have to migrate databases later.

---

### Redis
**What it is:** A very fast, temporary, in-memory data store — think of it as a short-term memory cache, not permanent storage like Postgres.

**Why we need it:** Two future uses —
1. **Caching** — e.g., store today's stock prices for a few minutes so we don't re-fetch them from Yahoo Finance on every single page load.
2. **Job queue** — for slow tasks (Monte Carlo simulations, backtests), Redis lets the app say "start this job, I'll check back later" instead of making the user's browser freeze while waiting.

---

### Prisma
**What it is:** A tool that lets our Node.js (`apps/api`) code talk to Postgres using JavaScript, instead of writing raw SQL by hand.

**Why we used it:** It also manages **migrations** — a clean, trackable history of every change made to the database structure (e.g., "added a `users` table on this date"). This matters for the "proper Git discipline" goal from your V2 plan — every database change becomes a reviewable file in Git.

**The file `apps/api/prisma/schema.prisma`** is where we describe what tables exist. Right now it only has a placeholder `HealthCheck` table — real tables (`User`, `Portfolio`, etc.) get added phase by phase.

---

### SQLAlchemy (async) + asyncpg
**What it is:** The Python equivalent of Prisma — lets `apps/ai-service` (our Python app) talk to the same Postgres database.

**Why both api AND ai-service connect to Postgres separately:** They're two different programming languages (JavaScript vs Python), so each needs its own way of talking to the database — but they both point at the **same** Postgres database, so there's only one source of truth for the data.

**"async"/"asyncpg" specifically:** Python can either wait for one task to fully finish before starting the next (*slow*), or handle many things at once without blocking (*async*, faster). Since ai-service will eventually run heavy calculations (Monte Carlo, ML models) while also answering database queries, we set it up to be async from day one.

---

### FastAPI
**What it is:** The framework (a pre-built structure) our Python app (`ai-service`) uses to expose itself as a web service — i.e., turn Python functions into URLs that `apps/api` can call, like `http://localhost:8000/health`.

**Why FastAPI specifically:** It's fast, has good automatic documentation (visit `/docs` on the running service to see all available endpoints), and was already used in V1 — no new learning curve.

---

### Express
**What it is:** The framework `apps/api` (Node.js) uses to expose its own URLs, like `http://localhost:4000/api/health`. It's the most common way to build a web server in JavaScript.

---

### Vite
**What it is:** The tool that runs and builds our React website (`apps/web`) during development. When you run `npm run dev` inside `apps/web`, Vite starts a local server and refreshes the browser automatically every time you save a file.

**Why Vite over other options:** It's fast and was already the choice in V1 — again, no new learning curve.

---

### React
**What it is:** The library used to build the actual user interface — buttons, pages, charts, etc. — as reusable pieces called "components." `HealthCheckPage.jsx` is our first component.

---

### Tailwind CSS
**What it is:** A way of styling the website by adding small utility class names directly in the HTML/JSX (like `bg-paper text-ink font-serif`) instead of writing separate CSS files.

**Why:** Matches V1's approach, and we carried over the exact same color palette (`ink`, `paper`, `slate`, `brass`, `gain`, `risk`) so the visual identity stays consistent from V1.

---

### axios
**What it is:** A small library used to make HTTP requests — i.e., how `apps/web` calls `apps/api`, and how `apps/api` calls `apps/ai-service`. Think of it as "the thing that actually sends the request over the internet/network and waits for a reply."

---

### npm / package.json
**What it is:** Node.js's package manager. `package.json` lists every external library a Node/React app depends on (Express, Prisma, React, etc.). Running `npm install` reads that file and downloads everything listed into a `node_modules` folder (which we never commit to Git — see `.gitignore`).

---

### pip / requirements.txt
**What it is:** The Python equivalent of npm/package.json. `requirements.txt` lists Python libraries (FastAPI, SQLAlchemy, etc.), and `pip install -r requirements.txt` installs them.

---

### Git / GitHub Actions (CI)
**What it is:** Git tracks every change to your code over time (so you can undo mistakes, see history, collaborate). GitHub Actions (the `.github/workflows/ci.yml` file) automatically runs checks (like "does the code still build?") every time you push code — this is what "CI" (Continuous Integration) means.

**Why we set it up now, even with barely any code:** So it's a habit from day one, not something bolted on later when there's already a huge codebase to catch up on.

---

## Why we structured folders this way

Each app (`web`, `api`, `ai-service`) is organized into **feature folders** rather than dumping everything into generic folders like `components/` or `routes/`. For example, once Phase 1 (Market Dashboard) is built, everything related to it — the page, the API calls, the backend logic — will live together under a folder literally called `markets/`, in each app.

**Why this matters:** In V1, adding one feature (the Optimize page) meant touching 6+ scattered folders across 2 apps. Grouping by feature means when you want to find or change something about "market data," you look in one obviously-named place, not six.

---

## What "the health check" actually proved

The `/` page you saw with 4 green "ok" statuses proved this chain works:

```
Your browser (web)
      ↓ (axios call)
apps/api (Node/Express)
      ↓ (checks) → Postgres ✅
      ↓ (checks) → Redis ✅
      ↓ (axios call)
apps/ai-service (Python/FastAPI)
      ↓ (checks) → Postgres ✅ (same database, different app connecting to it)
```

If any one piece had been broken (e.g., Docker not running, wrong password in `.env`, ai-service not started), one of those four checks would have shown an error instead of "ok" — which is exactly why we built this check first, before writing any real feature.

---

## What's next

**Phase 1 — Public Market Dashboard**: the first real, visible feature. Live stock prices, market indices, charts, and top gainers/losers — visible without needing to log in.