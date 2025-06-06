"""Job status and type definitions for background processing."""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class JobStatus(Enum):
    """Job execution status."""

    PENDING = "pending"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class JobType(Enum):
    """Types of background jobs."""

    SCRAPING = "scraping"
    DATA_PROCESSING = "data_processing"
    LEAD_SCORING = "lead_scoring"
    ANALYTICS = "analytics"
    EXPORT = "export"
    MAINTENANCE = "maintenance"


class JobPriority(Enum):
    """Job priority levels."""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class JobProgress:
    """Job progress information."""

    current: int = 0
    total: int = 0
    percentage: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def update(self, current: int, total: int, message: str = "", **details):
        """Update progress information."""
        self.current = current
        self.total = total
        self.percentage = (current / total * 100) if total > 0 else 0.0
        self.message = message
        self.details.update(details)


@dataclass
class JobResult:
    """Job execution result."""

    job_id: str
    status: JobStatus
    job_type: JobType
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: JobProgress = field(default_factory=JobProgress)
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """Check if job is completed (success or failure)."""
        return self.status in [JobStatus.SUCCESS, JobStatus.FAILURE]

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status in [JobStatus.STARTED, JobStatus.PROGRESS]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "job_type": self.job_type.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": {
                "current": self.progress.current,
                "total": self.progress.total,
                "percentage": self.progress.percentage,
                "message": self.progress.message,
                "details": self.progress.details,
            },
            "result_data": self.result_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "duration": self.duration,
            "metadata": self.metadata,
        }
