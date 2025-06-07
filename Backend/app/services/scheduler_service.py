"""Scheduler service for automated monitoring and maintenance tasks."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

from app.services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled monitoring and maintenance tasks."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.monitoring = get_monitoring_service()
        self.is_running = False

    def start(self) -> None:
        """Start the scheduler and all scheduled tasks."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Schedule performance metrics recording every 5 minutes
            self.scheduler.add_job(
                func=self._record_performance_metrics,
                trigger=IntervalTrigger(minutes=5),
                id="record_performance_metrics",
                name="Record Performance Metrics",
                replace_existing=True,
            )

            # Schedule comprehensive health check every 15 minutes
            self.scheduler.add_job(
                func=self._comprehensive_health_check,
                trigger=IntervalTrigger(minutes=15),
                id="comprehensive_health_check",
                name="Comprehensive Health Check",
                replace_existing=True,
            )

            # Schedule daily system report at 6 AM
            self.scheduler.add_job(
                func=self._generate_daily_report,
                trigger=CronTrigger(hour=6, minute=0),
                id="daily_system_report",
                name="Daily System Report",
                replace_existing=True,
            )

            # Schedule weekly cleanup at Sunday 2 AM
            self.scheduler.add_job(
                func=self._weekly_cleanup,
                trigger=CronTrigger(day_of_week=6, hour=2, minute=0),
                id="weekly_cleanup",
                name="Weekly Cleanup",
                replace_existing=True,
            )

            # Schedule alert check every 2 minutes
            self.scheduler.add_job(
                func=self._check_and_process_alerts,
                trigger=IntervalTrigger(minutes=2),
                id="check_alerts",
                name="Check and Process Alerts",
                replace_existing=True,
            )

            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler service started successfully")

        except Exception as e:
            logger.error(f"Failed to start scheduler service: {e}")
            raise

    def stop(self) -> None:
        """Stop the scheduler and all scheduled tasks."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler service stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop scheduler service: {e}")
            raise

    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs."""
        jobs = self.scheduler.get_jobs()

        job_status = {
            "scheduler_running": self.is_running,
            "total_jobs": len(jobs),
            "jobs": [],
        }

        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
                "trigger": str(job.trigger),
                "func_name": (
                    job.func.__name__
                    if hasattr(job.func, "__name__")
                    else str(job.func)
                ),
            }
            job_status["jobs"].append(job_info)

        return job_status

    async def _record_performance_metrics(self) -> None:
        """Scheduled task to record performance metrics."""
        try:
            logger.debug("Recording performance metrics...")
            self.monitoring.record_performance_metrics()
            logger.debug("Performance metrics recorded successfully")

        except Exception as e:
            logger.error(f"Failed to record performance metrics: {e}")
            self.monitoring.log_error(e, "scheduled_performance_metrics")

    async def _comprehensive_health_check(self) -> None:
        """Scheduled task to perform comprehensive health check."""
        try:
            logger.debug("Performing comprehensive health check...")
            health_data = self.monitoring.get_comprehensive_health()

            # Log health status
            health_score = health_data.get("overall_health_score", 0)
            status = health_data.get("status", "unknown")

            logger.info(
                f"System health check completed - Score: {health_score}, Status: {status}"
            )

            # Log any critical alerts
            alerts = health_data.get("alerts", [])
            critical_alerts = [
                alert for alert in alerts if alert.get("level") == "critical"
            ]

            if critical_alerts:
                logger.warning(
                    f"Found {len(critical_alerts)} critical alerts during health check"
                )
                for alert in critical_alerts:
                    logger.warning(
                        f"Critical Alert - {alert.get('service')}: {alert.get('message')}"
                    )

        except Exception as e:
            logger.error(f"Failed to perform comprehensive health check: {e}")
            self.monitoring.log_error(e, "scheduled_health_check")

    async def _generate_daily_report(self) -> None:
        """Scheduled task to generate daily system report."""
        try:
            logger.info("Generating daily system report...")

            # Get 24-hour performance trends
            trends = self.monitoring.get_performance_trends(hours=24)

            # Get current health status
            health_data = self.monitoring.get_comprehensive_health()

            # Create summary report
            report = {
                "date": datetime.utcnow().date().isoformat(),
                "generated_at": datetime.utcnow().isoformat(),
                "health_summary": {
                    "overall_score": health_data.get("overall_health_score", 0),
                    "status": health_data.get("status", "unknown"),
                    "environment": health_data.get("environment", "unknown"),
                },
                "performance_trends": trends,
                "service_status": health_data.get("services", {}),
                "alerts_24h": len(health_data.get("alerts", [])),
            }

            logger.info(
                f"Daily report generated - Health Score: {report['health_summary']['overall_score']}, "
                f"Status: {report['health_summary']['status']}, "
                f"Alerts: {report['alerts_24h']}"
            )

            # In a production environment, you might want to:
            # - Send this report via email
            # - Store it in a database
            # - Send to monitoring dashboard
            # - Export to external monitoring service

        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")
            self.monitoring.log_error(e, "scheduled_daily_report")

    async def _weekly_cleanup(self) -> None:
        """Scheduled task to perform weekly cleanup operations."""
        try:
            logger.info("Performing weekly cleanup...")

            # Clear old performance history (keep only last 100 entries)
            if hasattr(self.monitoring, "performance_history"):
                history_length = len(self.monitoring.performance_history)
                if history_length > 100:
                    self.monitoring.performance_history = (
                        self.monitoring.performance_history[-100:]
                    )
                    logger.info(
                        f"Cleaned up performance history: removed {history_length - 100} old entries"
                    )

            # Clear resolved alerts older than 7 days
            if hasattr(self.monitoring, "alerts"):
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                initial_count = len(self.monitoring.alerts)
                self.monitoring.alerts = [
                    alert
                    for alert in self.monitoring.alerts
                    if not (alert.resolved and alert.timestamp < cutoff_date)
                ]
                cleaned_count = initial_count - len(self.monitoring.alerts)
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} old resolved alerts")

            # Clear old Redis error entries (if Redis is available)
            if self.monitoring.redis_client:
                try:
                    # Get all error keys
                    error_keys = self.monitoring.redis_client.keys("error:*")
                    cutoff_timestamp = (
                        datetime.utcnow() - timedelta(days=7)
                    ).timestamp()

                    cleaned_keys = 0
                    for key in error_keys:
                        try:
                            # Extract timestamp from key
                            timestamp_str = key.split(":")[1]
                            if float(timestamp_str) < cutoff_timestamp:
                                self.monitoring.redis_client.delete(key)
                                cleaned_keys += 1
                        except (ValueError, IndexError):
                            continue

                    if cleaned_keys > 0:
                        logger.info(
                            f"Cleaned up {cleaned_keys} old error entries from Redis"
                        )

                except Exception as redis_error:
                    logger.warning(
                        f"Failed to cleanup Redis error entries: {redis_error}"
                    )

            logger.info("Weekly cleanup completed successfully")

        except Exception as e:
            logger.error(f"Failed to perform weekly cleanup: {e}")
            self.monitoring.log_error(e, "scheduled_weekly_cleanup")

    async def _check_and_process_alerts(self) -> None:
        """Scheduled task to check and process system alerts."""
        try:
            logger.debug("Checking system alerts...")

            # Get current health data which includes alerts
            health_data = self.monitoring.get_comprehensive_health()
            alerts = health_data.get("alerts", [])

            # Process critical alerts
            critical_alerts = [
                alert for alert in alerts if alert.get("level") == "critical"
            ]

            if critical_alerts:
                logger.warning(f"Processing {len(critical_alerts)} critical alerts")

                for alert in critical_alerts:
                    # In a production environment, you might want to:
                    # - Send notifications (email, Slack, PagerDuty)
                    # - Trigger automated remediation
                    # - Update external monitoring systems
                    # - Create incident tickets

                    logger.critical(
                        f"CRITICAL ALERT - {alert.get('service', 'unknown')}: "
                        f"{alert.get('message', 'No message')} - "
                        f"{alert.get('details', 'No details')}"
                    )

            # Process high priority alerts
            high_alerts = [alert for alert in alerts if alert.get("level") == "high"]

            if high_alerts:
                logger.warning(f"Processing {len(high_alerts)} high priority alerts")

                for alert in high_alerts:
                    logger.warning(
                        f"HIGH ALERT - {alert.get('service', 'unknown')}: "
                        f"{alert.get('message', 'No message')}"
                    )

            logger.debug(
                f"Alert check completed - {len(alerts)} total alerts processed"
            )

        except Exception as e:
            logger.error(f"Failed to check and process alerts: {e}")
            self.monitoring.log_error(e, "scheduled_alert_check")

    def add_custom_job(self, func, trigger, job_id: str, name: str, **kwargs) -> None:
        """Add a custom scheduled job."""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                replace_existing=True,
                **kwargs,
            )
            logger.info(f"Added custom job: {name} ({job_id})")

        except Exception as e:
            logger.error(f"Failed to add custom job {job_id}: {e}")
            raise

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")

        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            raise


# Global scheduler service instance
scheduler_service = SchedulerService()


def get_scheduler_service() -> SchedulerService:
    """Get the global scheduler service instance."""
    return scheduler_service
