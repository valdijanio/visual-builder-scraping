import asyncio
import logging
from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.config import settings

logger = logging.getLogger(__name__)


class BrowserPool:
    """Pool of browser contexts for scraping."""

    def __init__(self):
        self.playwright = None
        self.browser: Browser | None = None
        self.contexts: asyncio.Queue[BrowserContext] = asyncio.Queue()
        self._size = settings.browser_pool_size
        self._initialized = False

    async def start(self):
        """Initialize browser and create context pool."""
        if self._initialized:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.browser_headless,
        )

        # Create initial contexts
        for _ in range(self._size):
            context = await self._create_context()
            await self.contexts.put(context)

        self._initialized = True
        logger.info(f"Browser pool started with {self._size} contexts")

    async def stop(self):
        """Close all contexts and browser."""
        if not self._initialized:
            return

        # Close all contexts
        while not self.contexts.empty():
            try:
                context = self.contexts.get_nowait()
                await context.close()
            except Exception:
                pass

        # Close browser
        if self.browser:
            await self.browser.close()

        # Stop playwright
        if self.playwright:
            await self.playwright.stop()

        self._initialized = False
        logger.info("Browser pool stopped")

    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with default settings."""
        return await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

    @asynccontextmanager
    async def get_page(self) -> Page:
        """Get a page from the pool. Returns page to pool when done."""
        if not self._initialized:
            raise RuntimeError("Browser pool not initialized")

        # Get context from pool
        context = await self.contexts.get()

        try:
            # Create new page
            page = await context.new_page()
            yield page
        finally:
            # Close page
            try:
                await page.close()
            except Exception:
                pass

            # Return context to pool (or create new one if broken)
            try:
                # Test if context is still valid
                await context.pages()
                await self.contexts.put(context)
            except Exception:
                # Context is broken, create new one
                try:
                    await context.close()
                except Exception:
                    pass
                new_context = await self._create_context()
                await self.contexts.put(new_context)


# Global browser pool instance
browser_pool = BrowserPool()
