from pydantic import BaseModel
from enum import Enum

class VideoGenerationRequest(BaseModel):
    text: str

class JobStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatusEnum
    result_url: str | None = None
    error: str | None = None

class JobSummary(BaseModel):
    job_id: str
    status: JobStatusEnum
