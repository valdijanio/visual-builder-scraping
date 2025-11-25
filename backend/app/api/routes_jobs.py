import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import JobCreate, JobResponse, JobStatus
from app.core.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
async def list_jobs(status: JobStatus | None = None):
    """List all jobs in memory."""
    jobs = manager.list_jobs(status=status.value if status else None)
    return [
        JobResponse(
            id=job["id"],
            template_id=job["template_id"],
            url=job["url"],
            status=job["status"],
            created_at=job["created_at"],
            started_at=job.get("started_at"),
            finished_at=job.get("finished_at"),
        )
        for job in jobs
    ]


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(data: JobCreate):
    """Create a new job and enqueue it."""
    from app.core.database import db

    # Validate template exists
    template = await db.fetchrow("SELECT id FROM scrape_templates WHERE id = $1", data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    job = await manager.create_job(template_id=data.template_id, url=data.url)

    return JobResponse(
        id=job["id"],
        template_id=job["template_id"],
        url=job["url"],
        status=job["status"],
        created_at=job["created_at"],
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status."""
    job = manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=job["id"],
        template_id=job["template_id"],
        url=job["url"],
        status=job["status"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        finished_at=job.get("finished_at"),
    )
