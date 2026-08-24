# FILE LOCATION: quantai/apps/ai-service/app/main.py
from dotenv import load_dotenv

load_dotenv()  # MUST run before other imports that read env vars (see V1 bug #4 lesson)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, markets

app = FastAPI(title="QuantAI AI Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in later phases once auth exists
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(markets.router, prefix="/api/markets")

# Future phases register their own routers here, e.g.:
# from app.api import optimization, simulation, backtest, assistant
# app.include_router(optimization.router, prefix="/api/optimization")