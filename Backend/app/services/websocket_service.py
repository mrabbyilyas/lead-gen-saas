import asyncio
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.models.schemas import (
    WebSocketMessage,
    JobProgressUpdate,
    LeadDiscoveryNotification,
)
from app.services.background_jobs import JobStatus

logger = logging.getLogger(__name__)


class WebSocketNotificationService:
    """Service for sending WebSocket notifications from background tasks."""

    def __init__(self):
        self._connection_manager = None
        self._loop = None

    def set_connection_manager(self, connection_manager):
        """Set the connection manager instance."""
        self._connection_manager = connection_manager

    def _get_event_loop(self):
        """Get or create event loop for async operations."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def _run_async(self, coro):
        """Run async coroutine from sync context."""
        if self._connection_manager is None:
            logger.warning("WebSocket connection manager not set")
            return

        try:
            loop = self._get_event_loop()
            if loop.is_running():
                # If loop is already running, schedule the coroutine
                asyncio.create_task(coro)
            else:
                # Run the coroutine
                loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Error running WebSocket notification: {e}")

    def notify_job_progress(
        self,
        job_id: str,
        status: JobStatus,
        progress_percentage: float,
        processed_targets: int,
        total_targets: int,
        companies_found: int = 0,
        contacts_found: int = 0,
        estimated_completion: Optional[datetime] = None,
        message: Optional[str] = None,
    ):
        """Send job progress notification."""
        try:
            progress_update = JobProgressUpdate(
                job_id=UUID(job_id),
                status=status.value,
                progress_percentage=Decimal(str(progress_percentage)),
                processed_targets=processed_targets,
                total_targets=total_targets,
                companies_found=companies_found,
                contacts_found=contacts_found,
                estimated_completion=estimated_completion,
                message=message
                or f"Job {status.value}: {progress_percentage:.1f}% complete",
            )

            # Import here to avoid circular imports
            from app.api.v1.endpoints.websocket import broadcast_job_progress

            self._run_async(broadcast_job_progress(job_id, progress_update))
            logger.debug(f"Sent job progress notification for {job_id}")

        except Exception as e:
            logger.error(f"Error sending job progress notification: {e}")

    def notify_lead_discovery(
        self,
        job_id: str,
        company_id: str,
        company_name: str,
        lead_score: float,
        contacts_found: int,
        key_insights: Optional[List[str]] = None,
    ):
        """Send lead discovery notification."""
        try:
            lead_notification = LeadDiscoveryNotification(
                job_id=UUID(job_id),
                company_id=UUID(company_id),
                company_name=company_name,
                lead_score=Decimal(str(lead_score)),
                contacts_found=contacts_found,
                key_insights=key_insights or [],
            )

            # Import here to avoid circular imports
            from app.api.v1.endpoints.websocket import broadcast_lead_discovery

            self._run_async(broadcast_lead_discovery(job_id, lead_notification))
            logger.debug(f"Sent lead discovery notification for {company_name}")

        except Exception as e:
            logger.error(f"Error sending lead discovery notification: {e}")

    def notify_job_completion(
        self,
        job_id: str,
        status: JobStatus,
        total_companies: int = 0,
        total_contacts: int = 0,
        job_type: Optional[str] = None,
        summary: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
    ):
        """Send job completion notification."""
        try:
            job_result = {
                "status": status.value,
                "total_companies": total_companies,
                "total_contacts": total_contacts,
                "job_type": job_type,
                "summary": summary or f"Job completed with status: {status.value}",
                "result_data": result_data or {},
            }

            # Import here to avoid circular imports
            from app.api.v1.endpoints.websocket import broadcast_job_completion

            self._run_async(broadcast_job_completion(job_id, job_result))
            logger.info(f"Sent job completion notification for {job_id}")

        except Exception as e:
            logger.error(f"Error sending job completion notification: {e}")

    def notify_job_error(
        self,
        job_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ):
        """Send job error notification."""
        try:
            error_data = {
                "job_id": job_id,
                "error_message": error_message,
                "error_details": error_details or {},
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Import here to avoid circular imports
            from app.api.v1.endpoints.websocket import connection_manager

            message = WebSocketMessage(type="job_error", data=error_data)

            self._run_async(connection_manager.broadcast_to_job(job_id, message))
            logger.warning(f"Sent job error notification for {job_id}: {error_message}")

        except Exception as e:
            logger.error(f"Error sending job error notification: {e}")

    def notify_system_event(
        self,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Send system-wide notification."""
        try:
            notification_data = {
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                **(data or {}),
            }

            # Import here to avoid circular imports
            from app.api.v1.endpoints.websocket import broadcast_system_notification

            self._run_async(
                broadcast_system_notification(event_type, notification_data)
            )
            logger.info(f"Sent system notification: {event_type} - {message}")

        except Exception as e:
            logger.error(f"Error sending system notification: {e}")

    def notify_batch_progress(
        self,
        job_id: str,
        batch_number: int,
        total_batches: int,
        batch_results: Dict[str, Any],
    ):
        """Send batch processing progress notification."""
        try:
            batch_progress = {
                "job_id": job_id,
                "batch_number": batch_number,
                "total_batches": total_batches,
                "batch_progress_percentage": (batch_number / total_batches) * 100,
                "batch_results": batch_results,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Import here to avoid circular imports
            from app.api.v1.endpoints.websocket import connection_manager

            message = WebSocketMessage(type="batch_progress", data=batch_progress)

            self._run_async(connection_manager.broadcast_to_job(job_id, message))
            logger.debug(
                f"Sent batch progress notification for {job_id}: {batch_number}/{total_batches}"
            )

        except Exception as e:
            logger.error(f"Error sending batch progress notification: {e}")

    def notify_data_quality_alert(
        self,
        job_id: str,
        alert_type: str,
        message: str,
        affected_records: int,
        severity: str = "warning",
    ):
        """Send data quality alert notification."""
        try:
            alert_data = {
                "job_id": job_id,
                "alert_type": alert_type,
                "message": message,
                "affected_records": affected_records,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Import here to avoid circular imports
            from app.api.v1.endpoints.websocket import connection_manager

            message_obj = WebSocketMessage(type="data_quality_alert", data=alert_data)

            self._run_async(connection_manager.broadcast_to_job(job_id, message_obj))
            logger.warning(
                f"Sent data quality alert for {job_id}: {alert_type} - {message}"
            )

        except Exception as e:
            logger.error(f"Error sending data quality alert: {e}")


# Global notification service instance
websocket_service = WebSocketNotificationService()


def get_websocket_service() -> WebSocketNotificationService:
    """Get the global WebSocket notification service instance."""
    return websocket_service
