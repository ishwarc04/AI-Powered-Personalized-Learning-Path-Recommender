"""
main.py — PathMind FastAPI application entry point.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import onboard, path, explain, chat, progress, dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PathMind API",
    description=(
        "AI-Powered Personalized Learning Path Recommender. "
        "Models skills as a prerequisite DAG and uses Grok LLM for adaptive path generation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(onboard.router)
app.include_router(path.router)
app.include_router(explain.router)
app.include_router(chat.router)
app.include_router(progress.router)
app.include_router(dashboard.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Initialising PathMind database...")
    init_db()
    logger.info("Database ready. PathMind API is live at http://localhost:8000/docs")


@app.get("/")
def root():
    return {
        "app": "PathMind",
        "status": "running",
        "docs": "http://localhost:8000/docs",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
