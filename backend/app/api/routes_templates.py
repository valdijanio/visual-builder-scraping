import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    TemplateCreate,
    TemplateResponse,
    TemplateTestRequest,
    TemplateTestResponse,
    TemplateUpdate,
)
from app.core.database import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])


def parse_jsonb(value):
    """Parse JSONB value that might be returned as string."""
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value


@router.get("", response_model=list[TemplateResponse])
async def list_templates(active_only: bool = False):
    """List all templates."""
    if active_only:
        rows = await db.fetch(
            "SELECT * FROM scrape_templates WHERE active = true ORDER BY created_at DESC"
        )
    else:
        rows = await db.fetch("SELECT * FROM scrape_templates ORDER BY created_at DESC")

    return [
        TemplateResponse(
            id=row["id"],
            name=row["name"],
            url_pattern=row["url_pattern"],
            selectors=parse_jsonb(row["selectors"]) or [],
            config=parse_jsonb(row["config"]) or {},
            active=row["active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(data: TemplateCreate):
    """Create a new template."""
    selectors_json = json.dumps([s.model_dump() for s in data.selectors])
    config_json = json.dumps(data.config)

    row = await db.fetchrow(
        """
        INSERT INTO scrape_templates (name, url_pattern, selectors, config)
        VALUES ($1, $2, $3::jsonb, $4::jsonb)
        RETURNING *
        """,
        data.name,
        data.url_pattern,
        selectors_json,
        config_json,
    )

    return TemplateResponse(
        id=row["id"],
        name=row["name"],
        url_pattern=row["url_pattern"],
        selectors=parse_jsonb(row["selectors"]) or [],
        config=parse_jsonb(row["config"]) or {},
        active=row["active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int):
    """Get template by ID."""
    row = await db.fetchrow("SELECT * FROM scrape_templates WHERE id = $1", template_id)

    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateResponse(
        id=row["id"],
        name=row["name"],
        url_pattern=row["url_pattern"],
        selectors=parse_jsonb(row["selectors"]) or [],
        config=parse_jsonb(row["config"]) or {},
        active=row["active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: int, data: TemplateUpdate):
    """Update template."""
    existing = await db.fetchrow("SELECT * FROM scrape_templates WHERE id = $1", template_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    # Build update fields
    updates = []
    values = []
    idx = 1

    if data.name is not None:
        updates.append(f"name = ${idx}")
        values.append(data.name)
        idx += 1

    if data.url_pattern is not None:
        updates.append(f"url_pattern = ${idx}")
        values.append(data.url_pattern)
        idx += 1

    if data.selectors is not None:
        updates.append(f"selectors = ${idx}::jsonb")
        values.append(json.dumps([s.model_dump() for s in data.selectors]))
        idx += 1

    if data.config is not None:
        updates.append(f"config = ${idx}::jsonb")
        values.append(json.dumps(data.config))
        idx += 1

    if data.active is not None:
        updates.append(f"active = ${idx}")
        values.append(data.active)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append(f"updated_at = ${idx}")
    values.append(datetime.now())
    idx += 1

    values.append(template_id)

    query = f"""
        UPDATE scrape_templates
        SET {', '.join(updates)}
        WHERE id = ${idx}
        RETURNING *
    """

    row = await db.fetchrow(query, *values)

    return TemplateResponse(
        id=row["id"],
        name=row["name"],
        url_pattern=row["url_pattern"],
        selectors=parse_jsonb(row["selectors"]) or [],
        config=parse_jsonb(row["config"]) or {},
        active=row["active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: int):
    """Delete template."""
    result = await db.execute("DELETE FROM scrape_templates WHERE id = $1", template_id)

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Template not found")


@router.post("/{template_id}/test", response_model=TemplateTestResponse)
async def test_template(template_id: int, data: TemplateTestRequest):
    """Test template by executing it on a URL."""
    from app.scraping.executor import executor

    template = await db.fetchrow("SELECT * FROM scrape_templates WHERE id = $1", template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        result = await executor.execute(
            url=data.url,
            selectors=parse_jsonb(template["selectors"]) or [],
        )
        return TemplateTestResponse(
            url=data.url,
            data=result["data"],
            duration_ms=result["duration_ms"],
        )
    except Exception as e:
        logger.error(f"Template test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
