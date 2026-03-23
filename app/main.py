from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.services.recommender import recommender
from app.api.routes import books, recommendations, search, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting BookRS API...")
    await init_db()
    await recommender.initialize()
    logger.info("✅ BookRS API ready!")
    yield
    # Shutdown
    logger.info("👋 Shutting down BookRS API...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Book Recommendation System",
    lifespan=lifespan,
)

# CORS for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(books.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "recommender_ready": recommender.is_ready,
    }
