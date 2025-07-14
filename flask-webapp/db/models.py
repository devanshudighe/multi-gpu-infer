from sqlalchemy import Column, String, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid

Base = declarative_base()

class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt = Column(Text, nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.pending)
    result_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)
