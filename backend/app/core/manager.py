import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages job queue and workers."""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.worker_tasks: list[asyncio.Task] = []
        self._running = False

    @property
    def worker_count(self) -> int:
        return len(self.worker_tasks)

    @property
    def pending_count(self) -> int:
        return sum(1 for j in self.jobs.values() if j["status"] == "pending")

    @property
    def running_count(self) -> int:
        return sum(1 for j in self.jobs.values() if j["status"] == "running")

    async def create_job(
        self,
        template_id: int,
        url: str,
        schedule_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new job and enqueue it."""
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "template_id": template_id,
            "schedule_id": schedule_id,
            "url": url,
            "status": "pending",
            "created_at": datetime.now(),
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
        }

        self.jobs[job_id] = job
        await self.queue.put(job_id)
        logger.info(f"Job {job_id} created and enqueued")

        return job

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def list_jobs(self, status: str | None = None) -> list[dict[str, Any]]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        return sorted(jobs, key=lambda j: j["created_at"], reverse=True)

    async def start_workers(self, count: int):
        """Start worker tasks."""
        from app.workers.scraper import ScraperWorker

        self._running = True

        for i in range(count):
            worker = ScraperWorker(self, i)
            task = asyncio.create_task(worker.run())
            self.worker_tasks.append(task)

        logger.info(f"Started {count} workers")

    async def stop_workers(self):
        """Stop all worker tasks."""
        self._running = False

        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Wait for all tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        self.worker_tasks.clear()
        logger.info("All workers stopped")

    def is_running(self) -> bool:
        return self._running

    def update_job(self, job_id: str, **kwargs):
        """Update job fields."""
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove old completed jobs from memory."""
        cutoff = datetime.now()
        to_remove = []

        for job_id, job in self.jobs.items():
            if job["status"] in ("success", "failed"):
                if job.get("finished_at"):
                    age = (cutoff - job["finished_at"]).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(job_id)

        for job_id in to_remove:
            del self.jobs[job_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")


# Global manager instance
manager = WorkerManager()
