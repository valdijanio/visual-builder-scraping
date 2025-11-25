import json
import logging
from datetime import datetime

from app.core.database import db
from app.scraping.executor import executor
from app.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class ScraperWorker(BaseWorker):
    """Worker that executes scraping jobs."""

    async def process(self, job: dict):
        """Process a scraping job."""
        job_id = job["id"]
        start_time = datetime.now()

        # Update job status to running
        self.manager.update_job(job_id, status="running", started_at=start_time)

        try:
            # Fetch template from database
            template = await db.fetchrow(
                "SELECT * FROM scrape_templates WHERE id = $1",
                job["template_id"],
            )

            if not template:
                raise ValueError(f"Template {job['template_id']} not found")

            # Execute scraping
            result = await executor.execute(
                url=job["url"],
                selectors=template["selectors"] or [],
            )

            # Calculate duration
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Save result to database
            await db.execute(
                """
                INSERT INTO scrape_results (template_id, schedule_id, url, status, data, duration_ms)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                """,
                job["template_id"],
                job.get("schedule_id"),
                job["url"],
                "success",
                json.dumps(result["data"]),
                duration_ms,
            )

            # Update job status
            self.manager.update_job(
                job_id,
                status="success",
                finished_at=end_time,
                result=result["data"],
            )

            logger.info(f"Job {job_id} completed successfully in {duration_ms}ms")

        except Exception as e:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            error_msg = str(e)

            # Save error result to database
            await db.execute(
                """
                INSERT INTO scrape_results (template_id, schedule_id, url, status, error, duration_ms)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                job["template_id"],
                job.get("schedule_id"),
                job["url"],
                "failed",
                error_msg,
                duration_ms,
            )

            # Update job status
            self.manager.update_job(
                job_id,
                status="failed",
                finished_at=end_time,
                error=error_msg,
            )

            logger.error(f"Job {job_id} failed: {error_msg}")
