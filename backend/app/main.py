from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import threading

from app.database import init_db
from app.services import llm_service
from app.routers import analyze, reports, integrity, campaigns, stats, analyze_image


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    threading.Thread(target=llm_service.precalentar, daemon=True).start()
    yield


app = FastAPI(title="Escudo Comunitario API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://escudo-comunitario-github-hz4ptjxpr-eloxb.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (analyze, reports, integrity, campaigns, stats, analyze_image):
    app.include_router(r.router, prefix="/api")