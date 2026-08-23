<!-- FILE LOCATION: quantai/README.md -->
# QuantAI V2

Explainable AI Decision Intelligence Platform for portfolio management.

## Folder structure

```
quantai/
├── apps/
│   ├── web/            React + Vite + Tailwind frontend
│   ├── api/             Node/Express gateway (auth, portfolios, proxy to ai-service)
│   └── ai-service/      Python/FastAPI (quant math, ML, simulation, backtest, RAG, LLM)
├── packages/
│   ├── shared-types/    Shared TS types between web and api
│   └── design-tokens/   Shared design system tokens (colors, fonts)
├── docs/                Architecture docs, API docs, ADRs
├── .github/workflows/   CI pipelines
└── docker-compose.yml   Postgres + Redis for local dev
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop (for Postgres + Redis)

## First-time setup

```bash
# 1. Start Postgres + Redis
docker compose up -d

# 2. Set up the API (Node)
cd apps/api
npm install
copy .env.example .env
# edit .env with your local values
npx prisma migrate dev --name init
npm run dev

# 3. Set up ai-service (Python), in a new terminal
cd apps/ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt --break-system-packages
    copy .env.example .env
uvicorn app.main:app --reload --port 8000

# 4. Set up web (React), in a new terminal
cd apps/web
npm install
npm run dev
```

Then open http://localhost:5173 for the frontend.

## Phase status

See `docs/architecture/phase-plan.md` for the full phase breakdown. Currently on **Phase 0 — Project Foundation**.
