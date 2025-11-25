from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# Enums
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class SelectorType(str, Enum):
    TEXT = "text"
    HTML = "html"
    ATTRIBUTE = "attribute"
    LIST = "list"


# Selector Field
class SelectorField(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    selector: str = Field(..., min_length=1)
    type: SelectorType = SelectorType.TEXT
    attribute: str | None = None  # Required if type=attribute


# Templates
class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url_pattern: str | None = None
    selectors: list[SelectorField] = []
    config: dict[str, Any] = {}


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    url_pattern: str | None = None
    selectors: list[SelectorField] | None = None
    config: dict[str, Any] | None = None
    active: bool | None = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    url_pattern: str | None
    selectors: list[SelectorField]
    config: dict[str, Any]
    active: bool
    created_at: datetime
    updated_at: datetime


class TemplateTestRequest(BaseModel):
    url: str = Field(..., min_length=1)


class TemplateTestResponse(BaseModel):
    url: str
    data: dict[str, Any]
    duration_ms: int


# Schedules
class ScheduleCreate(BaseModel):
    template_id: int
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1)
    cron_expression: str | None = None  # ex: '0 */6 * * *'
    interval_minutes: int | None = None  # alternative to cron
    is_enabled: bool = True


class ScheduleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    url: str | None = None
    cron_expression: str | None = None
    interval_minutes: int | None = None
    is_enabled: bool | None = None


class ScheduleResponse(BaseModel):
    id: int
    template_id: int
    name: str
    url: str
    cron_expression: str | None
    interval_minutes: int | None
    is_enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime


# Jobs
class JobCreate(BaseModel):
    template_id: int
    url: str = Field(..., min_length=1)


class JobResponse(BaseModel):
    id: str
    template_id: int
    url: str
    status: JobStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


# Results
class ResultResponse(BaseModel):
    id: int
    template_id: int | None
    schedule_id: int | None
    url: str
    status: str
    data: dict[str, Any] | None
    error: str | None
    duration_ms: int | None
    extracted_at: datetime


class ResultListResponse(BaseModel):
    items: list[ResultResponse]
    total: int
    page: int
    page_size: int


# Health
class HealthResponse(BaseModel):
    status: str
    workers: int
    jobs_pending: int
    jobs_running: int
    schedules_active: int
