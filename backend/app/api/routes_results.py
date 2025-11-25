import logging

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import ResultListResponse, ResultResponse
from app.core.database import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=ResultListResponse)
async def list_results(
    template_id: int | None = None,
    schedule_id: int | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List results with pagination and filters."""
    # Build WHERE clause
    conditions = []
    values = []
    idx = 1

    if template_id is not None:
        conditions.append(f"template_id = ${idx}")
        values.append(template_id)
        idx += 1

    if schedule_id is not None:
        conditions.append(f"schedule_id = ${idx}")
        values.append(schedule_id)
        idx += 1

    if status is not None:
        conditions.append(f"status = ${idx}")
        values.append(status)
        idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count total
    count_query = f"SELECT COUNT(*) FROM scrape_results {where_clause}"
    total = await db.fetchval(count_query, *values)

    # Fetch page
    offset = (page - 1) * page_size
    values.extend([page_size, offset])

    query = f"""
        SELECT * FROM scrape_results
        {where_clause}
        ORDER BY extracted_at DESC
        LIMIT ${idx} OFFSET ${idx + 1}
    """

    rows = await db.fetch(query, *values)

    items = [
        ResultResponse(
            id=row["id"],
            template_id=row["template_id"],
            schedule_id=row["schedule_id"],
            url=row["url"],
            status=row["status"],
            data=row["data"],
            error=row["error"],
            duration_ms=row["duration_ms"],
            extracted_at=row["extracted_at"],
        )
        for row in rows
    ]

    return ResultListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{result_id}", response_model=ResultResponse)
async def get_result(result_id: int):
    """Get result by ID."""
    row = await db.fetchrow("SELECT * FROM scrape_results WHERE id = $1", result_id)

    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    return ResultResponse(
        id=row["id"],
        template_id=row["template_id"],
        schedule_id=row["schedule_id"],
        url=row["url"],
        status=row["status"],
        data=row["data"],
        error=row["error"],
        duration_ms=row["duration_ms"],
        extracted_at=row["extracted_at"],
    )


@router.delete("/{result_id}", status_code=204)
async def delete_result(result_id: int):
    """Delete result."""
    result = await db.execute("DELETE FROM scrape_results WHERE id = $1", result_id)

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Result not found")
