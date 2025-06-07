"""Monitoring service for tracking application health, performance, and errors."""

import logging
import time
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

import redis
import psutil
from celery import Celery
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import test_database_connection
from app.services import get_system_metrics_service
from app.models.schemas import SystemMetricsCreate

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNAVAILABLE = "unavailable"


@dataclass
class Alert:
    """System alert data structure."""
    level: AlertLevel
    service: str
    message: str
    details: str
    timestamp: datetime
    resolved: bool = False


@dataclass
class ServiceHealth:
    """Service health information."""
    name: str
    status: ServiceStatus
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemPerformance:
    """System performance metrics."""
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    timestamp: datetime


class MonitoringService:
    """Comprehensive monitoring service for the application."""
    
    def __init__(self):
        self.redis_client = self._init_redis_client()
        self.celery_app = self._init_celery_app()
        self.alerts: List[Alert] = []
        self.performance_history: List[SystemPerformance] = []
        
    def _init_redis_client(self) -> Any:
        """Initialize Redis client for monitoring."""
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()  # Test connection
            return client
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")
            return None
    
    def _init_celery_app(self) -> Optional[Celery]:
        """Initialize Celery app for worker monitoring."""
        try:
            app = Celery('monitoring')
            app.config_from_object({
                'broker_url': settings.CELERY_BROKER_URL,
                'result_backend': settings.CELERY_RESULT_BACKEND,
            })
            return app
        except Exception as e:
            logger.warning(f"Failed to initialize Celery app: {e}")
            return None
    
    def check_database_health(self) -> ServiceHealth:
        """Check database connection and performance."""
        try:
            start_time = time.time()
            is_healthy = test_database_connection()
            response_time = (time.time() - start_time) * 1000
            
            status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
            
            return ServiceHealth(
                name="database",
                status=status,
                response_time_ms=round(response_time, 2),
                metadata={"type": "supabase"}
            )
        except Exception as e:
            return ServiceHealth(
                name="database",
                status=ServiceStatus.UNHEALTHY,
                error=str(e)
            )
    
    def check_redis_health(self) -> ServiceHealth:
        """Check Redis connection and performance."""
        if not self.redis_client:
            return ServiceHealth(
                name="redis",
                status=ServiceStatus.UNAVAILABLE,
                error="Redis client not initialized"
            )
        
        try:
            start_time = time.time()
            self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = self.redis_client.info()
            
            return ServiceHealth(
                name="redis",
                status=ServiceStatus.HEALTHY,
                response_time_ms=round(response_time, 2),
                metadata={
                    "connected_clients": info.get('connected_clients', 0),
                    "used_memory_mb": round(info.get('used_memory', 0) / (1024**2), 2),
                    "uptime_seconds": info.get('uptime_in_seconds', 0),
                }
            )
        except Exception as e:
            return ServiceHealth(
                name="redis",
                status=ServiceStatus.UNHEALTHY,
                error=str(e)
            )
    
    def check_celery_health(self) -> ServiceHealth:
        """Check Celery workers status."""
        if not self.celery_app:
            return ServiceHealth(
                name="celery",
                status=ServiceStatus.UNAVAILABLE,
                error="Celery app not initialized"
            )
        
        try:
            inspect = self.celery_app.control.inspect()
            active_workers = inspect.active()
            stats = inspect.stats()
            
            worker_count = len(active_workers) if active_workers else 0
            status = ServiceStatus.HEALTHY if worker_count > 0 else ServiceStatus.DEGRADED
            
            return ServiceHealth(
                name="celery",
                status=status,
                metadata={
                    "active_workers": worker_count,
                    "worker_stats": stats or {},
                }
            )
        except Exception as e:
            return ServiceHealth(
                name="celery",
                status=ServiceStatus.UNHEALTHY,
                error=str(e)
            )
    
    def get_system_performance(self) -> SystemPerformance:
        """Get current system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            performance = SystemPerformance(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                memory_available_gb=round(memory.available / (1024**3), 2),
                disk_usage_percent=disk.percent,
                disk_free_gb=round(disk.free / (1024**3), 2),
                timestamp=datetime.utcnow()
            )
            
            # Store in history (keep last 100 entries)
            self.performance_history.append(performance)
            if len(self.performance_history) > 100:
                self.performance_history.pop(0)
            
            return performance
            
        except Exception as e:
            logger.error(f"Error getting system performance: {e}")
            return SystemPerformance(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                memory_available_gb=0.0,
                disk_usage_percent=0.0,
                disk_free_gb=0.0,
                timestamp=datetime.utcnow()
            )
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        # Check all services
        db_health = self.check_database_health()
        redis_health = self.check_redis_health()
        celery_health = self.check_celery_health()
        performance = self.get_system_performance()
        
        # Calculate overall health score
        health_score = self._calculate_health_score(
            db_health, redis_health, celery_health, performance
        )
        
        # Generate alerts
        alerts = self._generate_alerts(
            db_health, redis_health, celery_health, performance
        )
        
        # Determine overall status
        overall_status = self._determine_overall_status(health_score)
        
        return {
            "overall_health_score": health_score,
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "version": settings.API_VERSION,
            "services": {
                "database": asdict(db_health),
                "redis": asdict(redis_health),
                "celery": asdict(celery_health),
            },
            "performance": asdict(performance),
            "alerts": [asdict(alert) for alert in alerts],
        }
    
    def _calculate_health_score(
        self, 
        db_health: ServiceHealth, 
        redis_health: ServiceHealth, 
        celery_health: ServiceHealth, 
        performance: SystemPerformance
    ) -> int:
        """Calculate overall health score (0-100)."""
        score = 100
        
        # Service health scoring
        if db_health.status == ServiceStatus.UNHEALTHY:
            score -= 40
        elif db_health.status == ServiceStatus.DEGRADED:
            score -= 20
        
        if redis_health.status == ServiceStatus.UNHEALTHY:
            score -= 30
        elif redis_health.status == ServiceStatus.DEGRADED:
            score -= 15
        
        if celery_health.status == ServiceStatus.UNHEALTHY:
            score -= 20
        elif celery_health.status == ServiceStatus.DEGRADED:
            score -= 10
        
        # Performance scoring
        if performance.cpu_usage_percent > 90:
            score -= 10
        elif performance.cpu_usage_percent > 80:
            score -= 5
        
        if performance.memory_usage_percent > 90:
            score -= 10
        elif performance.memory_usage_percent > 85:
            score -= 5
        
        if performance.disk_usage_percent > 90:
            score -= 10
        elif performance.disk_usage_percent > 85:
            score -= 5
        
        return max(0, score)
    
    def _determine_overall_status(self, health_score: int) -> str:
        """Determine overall system status based on health score."""
        if health_score >= 80:
            return "healthy"
        elif health_score >= 50:
            return "degraded"
        else:
            return "critical"
    
    def _generate_alerts(
        self, 
        db_health: ServiceHealth, 
        redis_health: ServiceHealth, 
        celery_health: ServiceHealth, 
        performance: SystemPerformance
    ) -> List[Alert]:
        """Generate system alerts based on health checks."""
        alerts = []
        timestamp = datetime.utcnow()
        
        # Service alerts
        if db_health.status == ServiceStatus.UNHEALTHY:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                service="database",
                message="Database connection is down",
                details=db_health.error or "Database health check failed",
                timestamp=timestamp
            ))
        
        if redis_health.status == ServiceStatus.UNHEALTHY:
            alerts.append(Alert(
                level=AlertLevel.HIGH,
                service="redis",
                message="Redis connection is down",
                details=redis_health.error or "Redis health check failed",
                timestamp=timestamp
            ))
        
        if celery_health.status == ServiceStatus.UNHEALTHY:
            alerts.append(Alert(
                level=AlertLevel.HIGH,
                service="celery",
                message="No Celery workers available",
                details=celery_health.error or "No active workers detected",
                timestamp=timestamp
            ))
        
        # Performance alerts
        if performance.cpu_usage_percent > 90:
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                service="system",
                message=f"High CPU usage: {performance.cpu_usage_percent:.1f}%",
                details="CPU usage is above 90%",
                timestamp=timestamp
            ))
        
        if performance.memory_usage_percent > 90:
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                service="system",
                message=f"High memory usage: {performance.memory_usage_percent:.1f}%",
                details="Memory usage is above 90%",
                timestamp=timestamp
            ))
        
        if performance.disk_usage_percent > 85:
            alerts.append(Alert(
                level=AlertLevel.MEDIUM,
                service="system",
                message=f"High disk usage: {performance.disk_usage_percent:.1f}%",
                details="Disk usage is above 85%",
                timestamp=timestamp
            ))
        
        return alerts
    
    def record_performance_metrics(self) -> None:
        """Record current performance metrics to database."""
        try:
            metrics_service = get_system_metrics_service()
            performance = self.get_system_performance()
            
            # Record CPU usage
            cpu_metric = SystemMetricsCreate(
                metric_name="cpu_usage_percent",
                metric_value=performance.cpu_usage_percent
            )
            metrics_service.record_metric(cpu_metric)
            
            # Record memory usage
            memory_metric = SystemMetricsCreate(
                metric_name="memory_usage_percent",
                metric_value=performance.memory_usage_percent
            )
            metrics_service.record_metric(memory_metric)
            
            # Record disk usage
            disk_metric = SystemMetricsCreate(
                metric_name="disk_usage_percent",
                metric_value=performance.disk_usage_percent
            )
            metrics_service.record_metric(disk_metric)
            
            logger.info("Performance metrics recorded successfully")
            
        except Exception as e:
            logger.error(f"Failed to record performance metrics: {e}")
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over the specified time period."""
        try:
            metrics_service = get_system_metrics_service()
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get CPU metrics
            cpu_metrics, _ = metrics_service.get_metrics(
                metric_name="cpu_usage_percent",
                start_time=start_time,
                end_time=end_time
            )
            
            # Get memory metrics
            memory_metrics, _ = metrics_service.get_metrics(
                metric_name="memory_usage_percent",
                start_time=start_time,
                end_time=end_time
            )
            
            # Calculate averages and peaks
            cpu_values = [m.metric_value for m in cpu_metrics]
            memory_values = [m.metric_value for m in memory_metrics]
            
            return {
                "time_period_hours": hours,
                "cpu_usage": {
                    "average": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0,
                    "peak": max(cpu_values) if cpu_values else 0,
                    "current": cpu_values[-1] if cpu_values else 0,
                },
                "memory_usage": {
                    "average": round(sum(memory_values) / len(memory_values), 2) if memory_values else 0,
                    "peak": max(memory_values) if memory_values else 0,
                    "current": memory_values[-1] if memory_values else 0,
                },
                "data_points": len(cpu_metrics),
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {
                "error": str(e),
                "time_period_hours": hours,
            }
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Log application errors for monitoring."""
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc(),
        }
        
        logger.error(f"Application error in {context}: {error}", extra=error_info)
        
        # Store error in Redis for quick access (if available)
        if self.redis_client:
            try:
                error_key = f"error:{datetime.utcnow().timestamp()}"
                self.redis_client.setex(error_key, 86400, str(error_info))  # Store for 24 hours
            except Exception as redis_error:
                logger.warning(f"Failed to store error in Redis: {redis_error}")


# Global monitoring service instance
monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    return monitoring_service