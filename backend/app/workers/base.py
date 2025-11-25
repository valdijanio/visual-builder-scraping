import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """Abstract base class for workers."""

    def __init__(self, manager, worker_id: int):
        self.manager = manager
        self.worker_id = worker_id
        self.name = f"{self.__class__.__name__}-{worker_id}"

    async def run(self):
        """Main worker loop."""
        logger.info(f"{self.name} started")

        while self.manager.is_running():
            try:
                # Wait for a job with timeout to allow checking if still running
                try:
                    job_id = await asyncio.wait_for(
                        self.manager.queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                job = self.manager.get_job(job_id)
                if not job:
                    logger.warning(f"Job {job_id} not found")
                    continue

                logger.info(f"{self.name} processing job {job_id}")
                await self.process(job)

            except asyncio.CancelledError:
                logger.info(f"{self.name} cancelled")
                break
            except Exception as e:
                logger.error(f"{self.name} error: {e}")

        logger.info(f"{self.name} stopped")

    @abstractmethod
    async def process(self, job: dict):
        """Process a single job. Must be implemented by subclasses."""
        pass
