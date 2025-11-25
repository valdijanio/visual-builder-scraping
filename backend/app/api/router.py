from fastapi import APIRouter

from app.api import routes_jobs, routes_results, routes_schedules, routes_templates
from app.api.schemas import HealthResponse
from app.core.manager import manager

router = APIRouter()

# Include sub-routers
router.include_router(routes_templates.router)
router.include_router(routes_schedules.router)
router.include_router(routes_jobs.router)
router.include_router(routes_results.router)


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    from app.core.database import db
    from app.scheduler.jobs import scheduler_manager

    # Count active schedules
    schedules_active = await db.fetchval(
        "SELECT COUNT(*) FROM scrape_schedules WHERE is_enabled = true"
    )

    return HealthResponse(
        status="healthy",
        workers=manager.worker_count,
        jobs_pending=manager.pending_count,
        jobs_running=manager.running_count,
        schedules_active=schedules_active or 0,
    )
