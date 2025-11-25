import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import db
from app.core.manager import manager

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manages APScheduler for scheduled scraping jobs."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            job_defaults={
                "coalesce": True,  # Combine multiple missed runs into one
                "max_instances": 1,  # Don't run same job concurrently
                "misfire_grace_time": 60,  # Grace period for missed jobs
            }
        )
        self._started = False

    async def start(self):
        """Start the scheduler and load schedules from database."""
        if self._started:
            return

        # Load all enabled schedules from database
        await self._load_schedules()

        # Start the scheduler
        self.scheduler.start()
        self._started = True
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Scheduler stopped")

    async def _load_schedules(self):
        """Load all enabled schedules from the database."""
        rows = await db.fetch(
            "SELECT * FROM scrape_schedules WHERE is_enabled = true"
        )

        for row in rows:
            await self._add_job(row)

        logger.info(f"Loaded {len(rows)} schedules from database")

    async def _add_job(self, schedule: dict):
        """Add a job to the scheduler based on schedule config."""
        schedule_id = schedule["id"]
        job_id = f"schedule_{schedule_id}"

        # Determine trigger type
        if schedule["cron_expression"]:
            try:
                trigger = CronTrigger.from_crontab(schedule["cron_expression"])
            except Exception as e:
                logger.error(f"Invalid cron expression for schedule {schedule_id}: {e}")
                return
        elif schedule["interval_minutes"]:
            trigger = IntervalTrigger(minutes=schedule["interval_minutes"])
        else:
            logger.warning(f"Schedule {schedule_id} has no cron or interval configured")
            return

        # Add job
        self.scheduler.add_job(
            self._execute_job,
            trigger=trigger,
            id=job_id,
            name=schedule["name"],
            args=[schedule_id],
            replace_existing=True,
        )

        # Update next_run_at in database
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            await db.execute(
                "UPDATE scrape_schedules SET next_run_at = $1 WHERE id = $2",
                job.next_run_time.replace(tzinfo=None),
                schedule_id,
            )

        logger.info(f"Added schedule {schedule_id} ({schedule['name']}) to scheduler")

    async def _execute_job(self, schedule_id: int):
        """Execute a scheduled scraping job."""
        logger.info(f"Executing schedule {schedule_id}")

        # Fetch schedule details
        schedule = await db.fetchrow(
            "SELECT * FROM scrape_schedules WHERE id = $1",
            schedule_id,
        )

        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return

        if not schedule["is_enabled"]:
            logger.info(f"Schedule {schedule_id} is disabled, skipping")
            return

        # Create job
        await manager.create_job(
            template_id=schedule["template_id"],
            url=schedule["url"],
            schedule_id=schedule_id,
        )

        # Update last_run_at and next_run_at
        job_id = f"schedule_{schedule_id}"
        job = self.scheduler.get_job(job_id)
        next_run = job.next_run_time.replace(tzinfo=None) if job and job.next_run_time else None

        await db.execute(
            "UPDATE scrape_schedules SET last_run_at = $1, next_run_at = $2 WHERE id = $3",
            datetime.now(),
            next_run,
            schedule_id,
        )

    async def add_schedule(self, schedule_id: int):
        """Add a new schedule to the scheduler."""
        schedule = await db.fetchrow(
            "SELECT * FROM scrape_schedules WHERE id = $1",
            schedule_id,
        )

        if schedule and schedule["is_enabled"]:
            await self._add_job(schedule)

    def remove_schedule(self, schedule_id: int):
        """Remove a schedule from the scheduler."""
        job_id = f"schedule_{schedule_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed schedule {schedule_id} from scheduler")
        except Exception:
            pass  # Job might not exist

    async def execute_schedule(self, schedule_id: int) -> str:
        """Execute a schedule immediately and return job_id."""
        schedule = await db.fetchrow(
            "SELECT * FROM scrape_schedules WHERE id = $1",
            schedule_id,
        )

        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        job = await manager.create_job(
            template_id=schedule["template_id"],
            url=schedule["url"],
            schedule_id=schedule_id,
        )

        # Update last_run_at
        await db.execute(
            "UPDATE scrape_schedules SET last_run_at = $1 WHERE id = $2",
            datetime.now(),
            schedule_id,
        )

        return job["id"]

    def get_job_info(self, schedule_id: int) -> dict | None:
        """Get information about a scheduled job."""
        job_id = f"schedule_{schedule_id}"
        job = self.scheduler.get_job(job_id)

        if not job:
            return None

        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time,
            "trigger": str(job.trigger),
        }


# Global scheduler manager instance
scheduler_manager = SchedulerManager()
