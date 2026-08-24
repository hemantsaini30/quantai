<!-- FILE LOCATION: quantai/docs/phases/phase-1-market-dashboard.md -->

# Phase 1 — Public Market Dashboard

## What this phase was about

Phase 0 proved the plumbing works (web, api, ai-service, databases all talk to each other). Phase 1 is the first **real, visible feature** — a homepage that works without logging in, showing live stock market data.

This directly matches the #1 stated improvement for V2: instead of an empty dashboard, a visitor gets something useful immediately.

---

## What we actually built

- **A market data engine** (in `ai-service`) that fetches live prices from Yahoo Finance for a starter list of Indian (NSE) and US stocks
- **Six pieces of market information**: index levels (NIFTY/SENSEX or S&P 500/Dow/NASDAQ), top gainers, top losers, most active stocks (by volume), sector performance, and a basic stock search
- **A market switcher** — toggle between India and US data
- **A full pipeline**: Python calculates the data → Node.js caches and serves it → React displays it, matching the pattern established in V1 and confirmed working in Phase 0

---

## New concepts introduced this phase — explained simply

### yfinance
**What it is:** A free Python library that pulls stock market data from Yahoo Finance — prices, historical charts, company info — without needing a paid API key or subscription.

**Why we use it:** Matches your "no paid APIs" principle from V1. It's not officially supported by Yahoo (it's a community project that reads Yahoo's public data), which is why occasionally it can be slow or briefly blocked — this is a known trade-off of using a free data source, not a bug in our code.

---

### `fast_info` (and a real bug we caught)

**What it is:** yfinance gives you two ways to get a stock's current price — a slow, detailed way (`ticker.info`, downloads a lot of data) and a fast, lightweight way (`ticker.fast_info`, just the essentials: price, previous close, volume). We use the fast one since the dashboard needs to check many stocks quickly.

**The bug we caught before it reached you:** `fast_info` looks like a dictionary but isn't one — you can't do `info.get("last_price")` (which Python allows without complaining, it just quietly returns nothing). You have to write `info.last_price` instead. I originally wrote the code the wrong way, tested it with **fake/mocked data that also happened to be wrong in the same way**, and everything passed — but a real live check against Yahoo Finance's actual data revealed every single number would have shown up blank on your dashboard.

**Why this matters to you as a lesson, not just trivia:** This is exactly why the project's testing philosophy (from V1) insists on live verification, not just automated tests — automated tests only catch mistakes you anticipated. I fixed the code, and added a specific test (`test_fetch_quote_snapshot_uses_attribute_access_not_dict_get`) that would fail loudly if this exact mistake ever crept back in.

---

### Redis caching (used for real, for the first time)

**What it is:** In Phase 0, Redis was just proven to be *running*. In Phase 1, we actually use it: every market data request is stored in Redis for 60 seconds. If two people load the dashboard within that window, the second person gets the cached answer instantly instead of us re-asking Yahoo Finance.

**Why this matters:** Real-world courtesy to the free data source (fewer requests = less likely to get rate-limited or blocked) and makes your dashboard feel faster. If Redis is ever briefly unavailable, the code is written to fall back to a live fetch rather than breaking the page — caching is a speed optimization, never a hard requirement.

---

### "Module" folder pattern (used for real, for the first time)

Every file for this feature lives under a folder literally called `markets/` in all three apps:
- `apps/ai-service/app/markets/` — the actual data-fetching logic
- `apps/ai-service/app/api/markets.py` — the URLs that expose that logic
- `apps/api/src/modules/markets/` — the Node.js middleman (service, controller, routes)
- `apps/web/src/features/markets/` — the React page and its pieces

**Why this matters:** If you ever want to find or change "how gainers are calculated," you know exactly where to look — one folder, not scattered across generic `services/` or `controllers/` folders shared by every feature.

---

### React components broken into small reusable pieces

Instead of one giant page file, the dashboard is split into:
- `MarketToggle.jsx` — the India/US switcher
- `IndexCard.jsx` — one card showing an index's price
- `StockTable.jsx` — a reusable table (used three times: gainers, losers, most active)
- `SectorPerformance.jsx` — the sector bar chart
- `StockSearch.jsx` — the search box
- `MarketDashboardPage.jsx` — the page that assembles all the pieces above

**Why this matters:** `StockTable.jsx` is a good example — it's used for gainers, losers, AND most-active, just with different data passed in. Writing it once and reusing it means one bug fix or style change applies everywhere it's used, instead of three separate places to update.

---

## What we tested, and how

Following the project's established testing philosophy:

- **Python (`ai-service`)**: 8 tests, all using **fake/mocked data** — no real network calls during testing (so tests run fast and don't depend on Yahoo Finance being reachable). Tests cover: correct price-change math, sorting gainers/losers correctly, averaging sector performance correctly, skipping a broken/delisted symbol without crashing the whole dashboard, and the `fast_info` bug fix described above.
- **Node.js (`api`)**: 6 tests, mocking both the network call to `ai-service` AND Redis, checking: cache hits skip the network call, cache misses fetch and then save to cache, a Redis outage doesn't break the feature, and errors from `ai-service` get translated into sensible HTTP status codes.
- **What I could NOT verify in my sandbox**: a full live boot of `apps/api` against a real Prisma-generated client and a full live boot of `apps/web` in a browser. My development sandbox has restricted internet access (it can't reach Prisma's binary download servers or Yahoo Finance directly), so these need to be checked on your machine, which has normal internet access. If anything unexpected happens when you run it, send me the exact error text and we'll debug it together.

---

## What "top gainers / losers / most active / sector performance" actually mean

In case these terms are new:

- **Top gainers** — stocks whose price went up the most (in %) since yesterday's close
- **Top losers** — stocks whose price went down the most (in %) since yesterday's close
- **Most active** — stocks with the highest trading volume (number of shares bought/sold) today, regardless of whether the price went up or down — high volume often means "lots of people are paying attention to this stock right now"
- **Sector performance** — stocks are grouped by industry (IT, Financials, Energy, etc.), and we show the average % change per group, so you can see "is IT having a good day, or a bad one?" at a glance

---

## Known limitations of this phase (intentional, not bugs)

- **Starter symbol list only** — 10 Indian and 10 US stocks are included as a demonstration set, not the full market. Expanding this list later is just adding entries to `universe.py`, nothing else needs to change.
- **Search is basic** — it only searches within that same starter list (matching name or symbol as text), not a live search across all of Yahoo Finance. Good enough for now; a real search index is a future improvement if the stock universe grows large.
- **No interactive price chart yet** — the backend has a `/history/{symbol}` endpoint ready (fetches historical daily prices), but no chart component was built on the frontend this phase. This can be added as a follow-up without any backend changes.
- **Sector performance is a simple average** — not weighted by company size (market cap). A big company moving 1% and a small company moving 1% count equally for now. This is a reasonable simplification for Phase 1; can be improved later.

---

## What's next

**Phase 2 — Authentication**: registration, login, logout, and protected routes — the gate that unlocks personalized features (portfolios, optimization, etc.) for logged-in users, while the market dashboard you just built stays open to everyone.