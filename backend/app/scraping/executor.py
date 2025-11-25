import logging
from datetime import datetime
from typing import Any

from app.scraping.browser import browser_pool

logger = logging.getLogger(__name__)


class TemplateExecutor:
    """Executes scraping templates using Playwright."""

    async def execute(self, url: str, selectors: list[dict]) -> dict[str, Any]:
        """
        Execute a template on a URL.

        Args:
            url: The URL to scrape
            selectors: List of selector definitions with format:
                - name: Field name
                - selector: CSS selector
                - type: text, html, attribute, list
                - attribute: Attribute name if type=attribute

        Returns:
            dict with:
                - data: Extracted data
                - duration_ms: Execution time in milliseconds
        """
        start_time = datetime.now()
        logger.info(f"Starting scrape of {url} with {len(selectors)} selectors")

        async with browser_pool.get_page() as page:
            # Navigate to URL - use domcontentloaded for faster loading
            # networkidle can timeout on sites with continuous requests (ads, analytics)
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for dynamic content to load
            await page.wait_for_timeout(3000)

            # Try to wait for the first selector to appear
            if selectors:
                first_selector = selectors[0].get("selector")
                if first_selector:
                    logger.info(f"Waiting for first selector: {first_selector}")
                    try:
                        await page.wait_for_selector(first_selector, timeout=10000)
                        logger.info("First selector found!")
                    except Exception as e:
                        logger.warning(f"First selector not found after 10s: {e}")
                        # Take screenshot for debugging
                        try:
                            screenshot = await page.screenshot()
                            logger.info(f"Page title: {await page.title()}")
                            logger.info(f"Page URL: {page.url}")
                        except:
                            pass

            # Extract data based on selectors
            data = {}
            for selector_def in selectors:
                name = selector_def.get("name")
                selector = selector_def.get("selector")
                selector_type = selector_def.get("type", "text")
                attribute = selector_def.get("attribute")

                if not name or not selector:
                    continue

                logger.info(f"Extracting '{name}' with selector: {selector}")

                try:
                    value = await self._extract_value(
                        page, selector, selector_type, attribute
                    )
                    logger.info(f"  Result for '{name}': {value[:100] if isinstance(value, str) and len(value) > 100 else value}")
                    data[name] = value
                except Exception as e:
                    logger.warning(f"Failed to extract '{name}': {e}")
                    data[name] = None

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.info(f"Scrape completed in {duration_ms}ms")

        return {
            "data": data,
            "duration_ms": duration_ms,
        }

    async def _extract_value(
        self,
        page,
        selector: str,
        selector_type: str,
        attribute: str | None,
    ) -> Any:
        """Extract a single value from the page."""
        if selector_type == "list":
            # Extract list of elements
            elements = await page.query_selector_all(selector)
            values = []
            for el in elements:
                text = await el.inner_text()
                values.append(text.strip() if text else None)
            return values

        # Single element extraction
        # Check if it's a Playwright pseudo-selector (:has-text)
        if ":has-text(" in selector:
            element = await self._extract_with_locator(page, selector)
        else:
            element = await page.query_selector(selector)

            # If CSS selector failed, try text-based fallback for common patterns
            if not element and ":nth-child" in selector:
                element = await self._try_text_fallback(page, selector)

        if not element:
            return None

        if selector_type == "text":
            text = await element.inner_text()
            return text.strip() if text else None

        elif selector_type == "html":
            return await element.inner_html()

        elif selector_type == "attribute":
            if not attribute:
                return None
            return await element.get_attribute(attribute)

        return None

    async def _extract_with_locator(self, page, selector: str):
        """
        Use Playwright locator API for pseudo-selectors like :has-text().
        """
        try:
            locator = page.locator(selector)
            count = await locator.count()
            if count > 0:
                return await locator.first.element_handle()
            return None
        except Exception as e:
            logger.warning(f"  Locator extraction failed: {e}")
            return None

    async def _try_text_fallback(self, page, selector: str):
        """
        Try to find element using text-based locator when CSS selector fails.
        This helps with fragile nth-child selectors.
        """
        try:
            # Extract the container ID from selector (e.g., #table-indicators)
            import re

            match = re.match(r"(#[\w-]+)", selector)
            if not match:
                return None

            container_id = match.group(1)
            logger.info(f"  Trying text-based fallback in container: {container_id}")

            # Get all cells in the container
            cells = await page.query_selector_all(f"{container_id} .cell")
            if not cells:
                cells = await page.query_selector_all(f"{container_id} > div")

            logger.info(f"  Found {len(cells)} cells in container")

            # Return None - the selector needs to be recaptured with better strategy
            return None
        except Exception as e:
            logger.warning(f"  Text fallback failed: {e}")
            return None


# Global executor instance
executor = TemplateExecutor()
