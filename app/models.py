from pydantic import BaseModel, Field
from typing import Any, Optional


class ScanRequest(BaseModel):
    number: int = Field(..., ge=0, description="Upper bound for CPU-heavy scan")


class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
