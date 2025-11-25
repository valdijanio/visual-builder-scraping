import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.api.schemas import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from app.core.database import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(enabled_only: bool = False):
    """List all schedules."""
    if enabled_only:
        rows = await db.fetch(
            "SELECT * FROM scrape_schedules WHERE is_enabled = true ORDER BY created_at DESC"
        )
    else:
        rows = await db.fetch("SELECT * FROM scrape_schedules ORDER BY created_at DESC")

    return [
        ScheduleResponse(
            id=row["id"],
            template_id=row["template_id"],
            name=row["name"],
            url=row["url"],
            cron_expression=row["cron_expression"],
            interval_minutes=row["interval_minutes"],
            is_enabled=row["is_enabled"],
            last_run_at=row["last_run_at"],
            next_run_at=row["next_run_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(data: ScheduleCreate):
    """Create a new schedule."""
    # Validate that either cron_expression or interval_minutes is provided
    if not data.cron_expression and not data.interval_minutes:
        raise HTTPException(
            status_code=400,
            detail="Either cron_expression or interval_minutes must be provided",
        )

    # Validate template exists
    template = await db.fetchrow("SELECT id FROM scrape_templates WHERE id = $1", data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    row = await db.fetchrow(
        """
        INSERT INTO scrape_schedules (template_id, name, url, cron_expression, interval_minutes, is_enabled)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        data.template_id,
        data.name,
        data.url,
        data.cron_expression,
        data.interval_minutes,
        data.is_enabled,
    )

    # Register with scheduler if enabled
    if data.is_enabled:
        from app.scheduler.jobs import scheduler_manager

        await scheduler_manager.add_schedule(row["id"])

    return ScheduleResponse(
        id=row["id"],
        template_id=row["template_id"],
        name=row["name"],
        url=row["url"],
        cron_expression=row["cron_expression"],
        interval_minutes=row["interval_minutes"],
        is_enabled=row["is_enabled"],
        last_run_at=row["last_run_at"],
        next_run_at=row["next_run_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int):
    """Get schedule by ID."""
    row = await db.fetchrow("SELECT * FROM scrape_schedules WHERE id = $1", schedule_id)

    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleResponse(
        id=row["id"],
        template_id=row["template_id"],
        name=row["name"],
        url=row["url"],
        cron_expression=row["cron_expression"],
        interval_minutes=row["interval_minutes"],
        is_enabled=row["is_enabled"],
        last_run_at=row["last_run_at"],
        next_run_at=row["next_run_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: int, data: ScheduleUpdate):
    """Update schedule."""
    existing = await db.fetchrow("SELECT * FROM scrape_schedules WHERE id = $1", schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Build update fields
    updates = []
    values = []
    idx = 1

    if data.name is not None:
        updates.append(f"name = ${idx}")
        values.append(data.name)
        idx += 1

    if data.url is not None:
        updates.append(f"url = ${idx}")
        values.append(data.url)
        idx += 1

    if data.cron_expression is not None:
        updates.append(f"cron_expression = ${idx}")
        values.append(data.cron_expression)
        idx += 1

    if data.interval_minutes is not None:
        updates.append(f"interval_minutes = ${idx}")
        values.append(data.interval_minutes)
        idx += 1

    if data.is_enabled is not None:
        updates.append(f"is_enabled = ${idx}")
        values.append(data.is_enabled)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append(f"updated_at = ${idx}")
    values.append(datetime.now())
    idx += 1

    values.append(schedule_id)

    query = f"""
        UPDATE scrape_schedules
        SET {', '.join(updates)}
        WHERE id = ${idx}
        RETURNING *
    """

    row = await db.fetchrow(query, *values)

    # Update scheduler
    from app.scheduler.jobs import scheduler_manager

    if data.is_enabled is False:
        scheduler_manager.remove_schedule(schedule_id)
    elif data.is_enabled is True or data.cron_expression or data.interval_minutes:
        scheduler_manager.remove_schedule(schedule_id)
        if row["is_enabled"]:
            await scheduler_manager.add_schedule(schedule_id)

    return ScheduleResponse(
        id=row["id"],
        template_id=row["template_id"],
        name=row["name"],
        url=row["url"],
        cron_expression=row["cron_expression"],
        interval_minutes=row["interval_minutes"],
        is_enabled=row["is_enabled"],
        last_run_at=row["last_run_at"],
        next_run_at=row["next_run_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: int):
    """Delete schedule."""
    # Remove from scheduler first
    from app.scheduler.jobs import scheduler_manager

    scheduler_manager.remove_schedule(schedule_id)

    result = await db.execute("DELETE FROM scrape_schedules WHERE id = $1", schedule_id)

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.post("/{schedule_id}/run", status_code=202)
async def run_schedule_now(schedule_id: int):
    """Execute schedule immediately."""
    schedule = await db.fetchrow("SELECT * FROM scrape_schedules WHERE id = $1", schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    from app.scheduler.jobs import scheduler_manager

    job_id = await scheduler_manager.execute_schedule(schedule_id)

    return {"message": "Schedule execution started", "job_id": job_id}
