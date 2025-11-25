import logging
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager using asyncpg."""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        """Create connection pool and initialize tables."""
        self.pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10,
        )
        logger.info("Database pool created")
        await self._create_tables()

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    async def _create_tables(self):
        """Create tables if they don't exist."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                -- Templates de scraping
                CREATE TABLE IF NOT EXISTS scrape_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    url_pattern TEXT,
                    selectors JSONB NOT NULL DEFAULT '[]',
                    config JSONB DEFAULT '{}',
                    active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                -- Agendamentos
                CREATE TABLE IF NOT EXISTS scrape_schedules (
                    id SERIAL PRIMARY KEY,
                    template_id INT REFERENCES scrape_templates(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    url TEXT NOT NULL,
                    cron_expression VARCHAR(100),
                    interval_minutes INT,
                    is_enabled BOOLEAN DEFAULT true,
                    last_run_at TIMESTAMP,
                    next_run_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                -- Resultados de scraping
                CREATE TABLE IF NOT EXISTS scrape_results (
                    id SERIAL PRIMARY KEY,
                    template_id INT REFERENCES scrape_templates(id),
                    schedule_id INT REFERENCES scrape_schedules(id),
                    url TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    data JSONB,
                    error TEXT,
                    duration_ms INT,
                    extracted_at TIMESTAMP DEFAULT NOW()
                );

                -- Índices
                CREATE INDEX IF NOT EXISTS idx_results_template ON scrape_results(template_id);
                CREATE INDEX IF NOT EXISTS idx_results_schedule ON scrape_results(schedule_id);
                CREATE INDEX IF NOT EXISTS idx_results_extracted ON scrape_results(extracted_at DESC);
                CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON scrape_schedules(is_enabled);
                CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON scrape_schedules(next_run_at);
            """)
            logger.info("Database tables created/verified")

    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        """Fetch multiple rows."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record | None:
        """Fetch a single row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn


# Global database instance
db = Database()
