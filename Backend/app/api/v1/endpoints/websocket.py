from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any
import json
import asyncio
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import logging

from app.models.schemas import (
    WebSocketMessage,
    JobProgressUpdate,
    LeadDiscoveryNotification,
)
from app.services.background_jobs import job_manager

router = APIRouter()
logger = logging.getLogger(__name__)


# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # Store active connections by job_id
        self.job_connections: Dict[str, Set[WebSocket]] = {}
        # Store general connections for system-wide notifications
        self.general_connections: Set[WebSocket] = set()
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect_to_job(self, websocket: WebSocket, job_id: str):
        """Connect a WebSocket to job-specific updates."""
        await websocket.accept()

        if job_id not in self.job_connections:
            self.job_connections[job_id] = set()

        self.job_connections[job_id].add(websocket)
        self.connection_metadata[websocket] = {
            "job_id": job_id,
            "connected_at": datetime.utcnow(),
            "type": "job_specific",
        }

        logger.info(f"WebSocket connected to job {job_id}")

        # Send initial job status
        await self._send_initial_job_status(websocket, job_id)

    async def connect_general(self, websocket: WebSocket):
        """Connect a WebSocket for general system notifications."""
        await websocket.accept()

        self.general_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "connected_at": datetime.utcnow(),
            "type": "general",
        }

        logger.info("WebSocket connected for general notifications")

        # Send welcome message
        await self._send_message(
            websocket,
            WebSocketMessage(
                type="connection_established",
                data={"message": "Connected to Lead Generation SaaS real-time updates"},
            ),
        )

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket and clean up."""
        metadata = self.connection_metadata.get(websocket, {})

        # Remove from job-specific connections
        if metadata.get("type") == "job_specific":
            job_id = metadata.get("job_id")
            if job_id and job_id in self.job_connections:
                self.job_connections[job_id].discard(websocket)
                if not self.job_connections[job_id]:
                    del self.job_connections[job_id]
                logger.info(f"WebSocket disconnected from job {job_id}")

        # Remove from general connections
        self.general_connections.discard(websocket)

        # Clean up metadata
        self.connection_metadata.pop(websocket, None)

    async def broadcast_to_job(self, job_id: str, message: WebSocketMessage):
        """Broadcast a message to all connections for a specific job."""
        if job_id not in self.job_connections:
            return

        disconnected = set()
        for websocket in self.job_connections[job_id].copy():
            try:
                await self._send_message(websocket, message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def broadcast_general(self, message: WebSocketMessage):
        """Broadcast a message to all general connections."""
        disconnected = set()
        for websocket in self.general_connections.copy():
            try:
                await self._send_message(websocket, message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def _send_message(self, websocket: WebSocket, message: WebSocketMessage):
        """Send a message to a specific WebSocket."""
        await websocket.send_text(message.model_dump_json())

    async def _send_initial_job_status(self, websocket: WebSocket, job_id: str):
        """Send initial job status when a client connects."""
        try:
            job_result = job_manager.get_job_status(job_id)
            if job_result:
                progress_update = JobProgressUpdate(
                    job_id=UUID(job_id),
                    status=job_result.status.value,
                    progress_percentage=Decimal(str(job_result.progress.percentage)),
                    processed_targets=job_result.progress.current,
                    total_targets=job_result.progress.total,
                    companies_found=job_result.progress.details.get(
                        "companies_found", 0
                    ),
                    contacts_found=job_result.progress.details.get("contacts_found", 0),
                    estimated_completion=None,
                    message=job_result.progress.message or "Job status retrieved",
                )

                message = WebSocketMessage(
                    type="job_progress", data=progress_update.model_dump()
                )

                await self._send_message(websocket, message)
            else:
                # Job not found
                error_message = WebSocketMessage(
                    type="error", data={"message": f"Job {job_id} not found"}
                )
                await self._send_message(websocket, error_message)
        except Exception as e:
            logger.error(f"Error sending initial job status: {e}")
            error_message = WebSocketMessage(
                type="error", data={"message": "Failed to retrieve job status"}
            )
            await self._send_message(websocket, error_message)

    def get_connection_count(self) -> Dict[str, int]:
        """Get current connection statistics."""
        job_connections_count = sum(
            len(connections) for connections in self.job_connections.values()
        )
        return {
            "total_connections": job_connections_count + len(self.general_connections),
            "job_specific_connections": job_connections_count,
            "general_connections": len(self.general_connections),
            "active_jobs": len(self.job_connections),
        }


# Global connection manager instance
connection_manager = ConnectionManager()


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_updates(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job progress updates.

    Provides real-time updates for:
    - Job progress and status changes
    - Lead discovery notifications
    - Job completion events
    - Error notifications
    """
    try:
        # Validate job_id format
        try:
            UUID(job_id)
        except ValueError:
            await websocket.close(code=1008, reason="Invalid job ID format")
            return

        # Check if job exists
        job_result = job_manager.get_job_status(job_id)
        if not job_result:
            await websocket.close(code=1008, reason="Job not found")
            return

        await connection_manager.connect_to_job(websocket, job_id)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (heartbeat, etc.)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle client messages
                try:
                    client_message = json.loads(data)
                    await _handle_client_message(websocket, job_id, client_message)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client: {data}")

            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                heartbeat = WebSocketMessage(
                    type="heartbeat", data={"timestamp": datetime.utcnow().isoformat()}
                )
                await connection_manager._send_message(websocket, heartbeat)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket)


@router.websocket("/ws/notifications")
async def websocket_general_notifications(websocket: WebSocket):
    """WebSocket endpoint for general system notifications.

    Provides real-time updates for:
    - System-wide announcements
    - New lead discoveries across all jobs
    - System health updates
    - General notifications
    """
    try:
        await connection_manager.connect_general(websocket)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)

                # Handle client messages
                try:
                    client_message = json.loads(data)
                    await _handle_general_client_message(websocket, client_message)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from general client: {data}")

            except asyncio.TimeoutError:
                # Send heartbeat
                heartbeat = WebSocketMessage(
                    type="heartbeat", data={"timestamp": datetime.utcnow().isoformat()}
                )
                await connection_manager._send_message(websocket, heartbeat)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected from general notifications")
    except Exception as e:
        logger.error(f"WebSocket error for general notifications: {e}")
    finally:
        await connection_manager.disconnect(websocket)


async def _handle_client_message(
    websocket: WebSocket, job_id: str, message: Dict[str, Any]
):
    """Handle messages from WebSocket clients for job-specific connections."""
    message_type = message.get("type")

    if message_type == "ping":
        # Respond to ping with pong
        pong = WebSocketMessage(
            type="pong", data={"timestamp": datetime.utcnow().isoformat()}
        )
        await connection_manager._send_message(websocket, pong)

    elif message_type == "get_status":
        # Send current job status
        await connection_manager._send_initial_job_status(websocket, job_id)

    elif message_type == "subscribe_events":
        # Client wants to subscribe to specific event types
        events = message.get("events", [])
        # Store subscription preferences (could be enhanced)
        logger.info(f"Client subscribed to events: {events} for job {job_id}")

    else:
        logger.warning(f"Unknown message type from client: {message_type}")


async def _handle_general_client_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle messages from WebSocket clients for general connections."""
    message_type = message.get("type")

    if message_type == "ping":
        # Respond to ping with pong
        pong = WebSocketMessage(
            type="pong", data={"timestamp": datetime.utcnow().isoformat()}
        )
        await connection_manager._send_message(websocket, pong)

    elif message_type == "get_stats":
        # Send connection statistics
        stats = connection_manager.get_connection_count()
        stats_message = WebSocketMessage(type="connection_stats", data=stats)
        await connection_manager._send_message(websocket, stats_message)

    else:
        logger.warning(f"Unknown message type from general client: {message_type}")


# Utility functions for broadcasting updates (to be called from background tasks)


async def broadcast_job_progress(job_id: str, progress_update: JobProgressUpdate):
    """Broadcast job progress update to all connected clients for a specific job."""
    message = WebSocketMessage(type="job_progress", data=progress_update.model_dump())
    await connection_manager.broadcast_to_job(job_id, message)


async def broadcast_lead_discovery(
    job_id: str, lead_notification: LeadDiscoveryNotification
):
    """Broadcast lead discovery notification."""
    # Send to job-specific connections
    job_message = WebSocketMessage(
        type="lead_discovered", data=lead_notification.model_dump()
    )
    await connection_manager.broadcast_to_job(job_id, job_message)

    # Also send to general connections
    general_message = WebSocketMessage(
        type="new_lead_discovered",
        data={**lead_notification.model_dump(), "source_job_id": job_id},
    )
    await connection_manager.broadcast_general(general_message)


async def broadcast_job_completion(job_id: str, job_result: Dict[str, Any]):
    """Broadcast job completion notification."""
    completion_message = WebSocketMessage(
        type="job_completed",
        data={
            "job_id": job_id,
            "status": job_result.get("status"),
            "total_companies": job_result.get("total_companies", 0),
            "total_contacts": job_result.get("total_contacts", 0),
            "completion_time": datetime.utcnow().isoformat(),
            "summary": job_result.get("summary", "Job completed successfully"),
        },
    )

    # Send to job-specific connections
    await connection_manager.broadcast_to_job(job_id, completion_message)

    # Send summary to general connections
    general_completion = WebSocketMessage(
        type="job_completed_notification",
        data={
            "job_id": job_id,
            "job_type": job_result.get("job_type"),
            "total_results": job_result.get("total_companies", 0)
            + job_result.get("total_contacts", 0),
            "completion_time": datetime.utcnow().isoformat(),
        },
    )
    await connection_manager.broadcast_general(general_completion)


async def broadcast_system_notification(notification_type: str, data: Dict[str, Any]):
    """Broadcast system-wide notifications."""
    message = WebSocketMessage(type=notification_type, data=data)
    await connection_manager.broadcast_general(message)


# Health check endpoint for WebSocket connections
@router.get("/ws/health")
async def websocket_health():
    """Get WebSocket connection health and statistics."""
    stats = connection_manager.get_connection_count()
    return {
        "status": "healthy",
        "websocket_connections": stats,
        "timestamp": datetime.utcnow().isoformat(),
    }
