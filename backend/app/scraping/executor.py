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

        async with browser_pool.get_page() as page:
            # Navigate to URL
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait a bit for dynamic content
            await page.wait_for_timeout(1000)

            # Extract data based on selectors
            data = {}
            for selector_def in selectors:
                name = selector_def.get("name")
                selector = selector_def.get("selector")
                selector_type = selector_def.get("type", "text")
                attribute = selector_def.get("attribute")

                if not name or not selector:
                    continue

                try:
                    value = await self._extract_value(
                        page, selector, selector_type, attribute
                    )
                    data[name] = value
                except Exception as e:
                    logger.warning(f"Failed to extract '{name}': {e}")
                    data[name] = None

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

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
        element = await page.query_selector(selector)
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


# Global executor instance
executor = TemplateExecutor()
