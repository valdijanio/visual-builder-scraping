import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.config import settings
from app.core.database import db
from app.core.manager import manager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application...")

    # Connect to database
    await db.connect()

    # Start workers
    await manager.start_workers(settings.worker_count)

    # Start scheduler
    from app.scheduler.jobs import scheduler_manager

    await scheduler_manager.start()

    # Start browser pool
    from app.scraping.browser import browser_pool

    await browser_pool.start()

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Stop scheduler
    scheduler_manager.stop()

    # Stop workers
    await manager.stop_workers()

    # Stop browser pool
    await browser_pool.stop()

    # Disconnect from database
    await db.disconnect()

    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api")
