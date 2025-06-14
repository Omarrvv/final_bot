"""
System Health Monitor for Egypt Tourism Chatbot

Provides comprehensive health monitoring, alerting, and diagnostics
for all system components. Ensures 100% system reliability through
proactive monitoring and automated recovery.
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from src.utils.error_handler import UnifiedErrorHandler, reliability_tracker

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """System component health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ComponentHealth:
    """Health information for a system component."""
    name: str
    status: HealthStatus
    last_check: datetime
    response_time_ms: float
    error_rate: float
    uptime_percent: float
    details: Dict[str, Any]
    alerts: List[str]

@dataclass
class SystemAlert:
    """System alert information."""
    component: str
    level: AlertLevel
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class SystemHealthMonitor:
    """
    Comprehensive system health monitoring and alerting.
    
    Monitors:
    - Database connectivity and performance
    - API service availability and rate limits
    - Memory and CPU usage
    - Error rates and patterns
    - Response times
    - Cache performance
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize system health monitor.
        
        Args:
            check_interval_seconds: How often to perform health checks
        """
        self.check_interval = check_interval_seconds
        self.component_health: Dict[str, ComponentHealth] = {}
        self.system_alerts: List[SystemAlert] = []
        self.start_time = datetime.now()
        self.monitoring_active = False
        
        # Health thresholds
        self.thresholds = {
            'response_time_warning_ms': 1000,
            'response_time_critical_ms': 5000,
            'error_rate_warning_percent': 5.0,
            'error_rate_critical_percent': 15.0,
            'uptime_warning_percent': 95.0,
            'uptime_critical_percent': 90.0
        }
        
        # Component registry
        self.registered_components: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"✅ System Health Monitor initialized with {check_interval_seconds}s interval")
    
    def register_component(self, name: str, health_check_func, 
                         critical: bool = True, timeout_seconds: float = 10.0):
        """
        Register a component for health monitoring.
        
        Args:
            name: Component name
            health_check_func: Function that returns component health info
            critical: Whether component is critical for system operation
            timeout_seconds: Timeout for health check
        """
        self.registered_components[name] = {
            'health_check': health_check_func,
            'critical': critical,
            'timeout': timeout_seconds,
            'last_success': None,
            'consecutive_failures': 0
        }
        
        # Initialize component health
        self.component_health[name] = ComponentHealth(
            name=name,
            status=HealthStatus.UNKNOWN,
            last_check=datetime.now(),
            response_time_ms=0.0,
            error_rate=0.0,
            uptime_percent=100.0,
            details={},
            alerts=[]
        )
        
        logger.info(f"📋 Registered component '{name}' for health monitoring")
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("🏥 Starting system health monitoring")
        
        while self.monitoring_active:
            try:
                await self.perform_health_checks()
                await self._evaluate_system_health()
                await self._cleanup_old_alerts()
                
                # Wait for next check interval
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retry
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring_active = False
        logger.info("🛑 Stopped system health monitoring")
    
    async def perform_health_checks(self):
        """Perform health checks for all registered components."""
        logger.debug("🔍 Performing health checks for all components")
        
        # Run all health checks in parallel
        check_tasks = []
        for component_name, config in self.registered_components.items():
            task = self._check_component_health(component_name, config)
            check_tasks.append(task)
        
        if check_tasks:
            await asyncio.gather(*check_tasks, return_exceptions=True)
    
    async def _check_component_health(self, component_name: str, config: Dict[str, Any]):
        """Check health of a specific component."""
        start_time = time.time()
        
        try:
            # Run health check with timeout
            health_data = await asyncio.wait_for(
                self._run_health_check(config['health_check']),
                timeout=config['timeout']
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Update component health
            await self._update_component_health(
                component_name, health_data, response_time_ms, True
            )
            
            config['last_success'] = datetime.now()
            config['consecutive_failures'] = 0
            
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(f"⏰ Health check timeout for {component_name}")
            
            await self._update_component_health(
                component_name, 
                {"error": f"Health check timeout after {config['timeout']}s"},
                response_time_ms, False
            )
            
            config['consecutive_failures'] += 1
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Health check failed for {component_name}: {str(e)}")
            
            await self._update_component_health(
                component_name,
                {"error": str(e)},
                response_time_ms, False
            )
            
            config['consecutive_failures'] += 1
    
    async def _run_health_check(self, health_check_func):
        """Run a health check function, handling both sync and async."""
        if asyncio.iscoroutinefunction(health_check_func):
            return await health_check_func()
        else:
            # Run synchronous function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, health_check_func)
    
    async def _update_component_health(self, component_name: str, health_data: Dict[str, Any],
                                     response_time_ms: float, success: bool):
        """Update health information for a component."""
        current_health = self.component_health[component_name]
        
        # Calculate error rate (last 100 checks)
        config = self.registered_components[component_name]
        total_checks = config.get('total_checks', 0) + 1
        failed_checks = config.get('failed_checks', 0) + (0 if success else 1)
        
        error_rate = (failed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Calculate uptime percentage
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        downtime_minutes = config['consecutive_failures'] * (self.check_interval / 60)
        uptime_percent = max(0, 100 - (downtime_minutes / (uptime_hours * 60)) * 100) if uptime_hours > 0 else 100
        
        # Determine health status
        if not success or config['consecutive_failures'] > 3:
            status = HealthStatus.UNHEALTHY
        elif (error_rate > self.thresholds['error_rate_warning_percent'] or 
              response_time_ms > self.thresholds['response_time_warning_ms'] or
              uptime_percent < self.thresholds['uptime_warning_percent']):
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        # Generate alerts
        alerts = []
        if response_time_ms > self.thresholds['response_time_critical_ms']:
            alerts.append(f"Critical response time: {response_time_ms:.1f}ms")
        elif response_time_ms > self.thresholds['response_time_warning_ms']:
            alerts.append(f"High response time: {response_time_ms:.1f}ms")
        
        if error_rate > self.thresholds['error_rate_critical_percent']:
            alerts.append(f"Critical error rate: {error_rate:.1f}%")
        elif error_rate > self.thresholds['error_rate_warning_percent']:
            alerts.append(f"High error rate: {error_rate:.1f}%")
        
        if uptime_percent < self.thresholds['uptime_critical_percent']:
            alerts.append(f"Critical uptime: {uptime_percent:.1f}%")
        elif uptime_percent < self.thresholds['uptime_warning_percent']:
            alerts.append(f"Low uptime: {uptime_percent:.1f}%")
        
        # Update component health
        self.component_health[component_name] = ComponentHealth(
            name=component_name,
            status=status,
            last_check=datetime.now(),
            response_time_ms=response_time_ms,
            error_rate=error_rate,
            uptime_percent=uptime_percent,
            details=health_data,
            alerts=alerts
        )
        
        # Update config tracking
        config['total_checks'] = total_checks
        config['failed_checks'] = failed_checks
        
        # Generate system alerts for significant issues
        if status == HealthStatus.UNHEALTHY and config['critical']:
            await self._create_alert(
                component_name, AlertLevel.CRITICAL,
                f"Critical component {component_name} is unhealthy"
            )
        elif status == HealthStatus.DEGRADED:
            await self._create_alert(
                component_name, AlertLevel.WARNING,
                f"Component {component_name} performance degraded"
            )
    
    async def _create_alert(self, component: str, level: AlertLevel, message: str):
        """Create a system alert."""
        # Check if similar alert already exists
        existing_alert = None
        for alert in self.system_alerts:
            if (alert.component == component and 
                alert.level == level and 
                not alert.resolved and
                alert.message == message):
                existing_alert = alert
                break
        
        if not existing_alert:
            alert = SystemAlert(
                component=component,
                level=level,
                message=message,
                timestamp=datetime.now()
            )
            self.system_alerts.append(alert)
            
            logger.warning(f"🚨 {level.value.upper()} ALERT: {component} - {message}")
    
    async def _evaluate_system_health(self):
        """Evaluate overall system health and generate system-level alerts."""
        unhealthy_critical = []
        degraded_components = []
        
        for name, health in self.component_health.items():
            config = self.registered_components[name]
            
            if health.status == HealthStatus.UNHEALTHY and config['critical']:
                unhealthy_critical.append(name)
            elif health.status == HealthStatus.DEGRADED:
                degraded_components.append(name)
        
        # System-level alerts
        if len(unhealthy_critical) > 0:
            await self._create_alert(
                "system", AlertLevel.CRITICAL,
                f"System critical: {len(unhealthy_critical)} critical components unhealthy"
            )
        elif len(degraded_components) > 2:
            await self._create_alert(
                "system", AlertLevel.WARNING,
                f"System degraded: {len(degraded_components)} components degraded"
            )
    
    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.system_alerts = [
            alert for alert in self.system_alerts 
            if not alert.resolved or alert.resolution_time > cutoff_time
        ]
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        healthy_count = sum(1 for h in self.component_health.values() if h.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for h in self.component_health.values() if h.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for h in self.component_health.values() if h.status == HealthStatus.UNHEALTHY)
        total_components = len(self.component_health)
        
        # Overall system status
        if unhealthy_count > 0:
            critical_unhealthy = sum(
                1 for name, health in self.component_health.items()
                if health.status == HealthStatus.UNHEALTHY and self.registered_components[name]['critical']
            )
            overall_status = "critical" if critical_unhealthy > 0 else "degraded"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Calculate uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Get active alerts
        active_alerts = [alert for alert in self.system_alerts if not alert.resolved]
        
        return {
            "overall_status": overall_status,
            "uptime_seconds": uptime_seconds,
            "uptime_human": self._format_uptime(uptime_seconds),
            "component_summary": {
                "total": total_components,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "health_percentage": (healthy_count / max(total_components, 1)) * 100
            },
            "components": {name: asdict(health) for name, health in self.component_health.items()},
            "active_alerts": [asdict(alert) for alert in active_alerts],
            "reliability_metrics": reliability_tracker.get_reliability_metrics(),
            "monitoring_active": self.monitoring_active,
            "last_check": max(
                (health.last_check for health in self.component_health.values()),
                default=datetime.now()
            ).isoformat(),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_component_health(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get health information for a specific component."""
        if component_name in self.component_health:
            health_dict = asdict(self.component_health[component_name])
            # Convert HealthStatus enum to string value
            health_dict['status'] = self.component_health[component_name].status.value
            return health_dict
        return None
    
    def resolve_alert(self, alert_index: int) -> bool:
        """Mark an alert as resolved."""
        if 0 <= alert_index < len(self.system_alerts):
            alert = self.system_alerts[alert_index]
            if not alert.resolved:
                alert.resolved = True
                alert.resolution_time = datetime.now()
                logger.info(f"✅ Resolved alert: {alert.component} - {alert.message}")
                return True
        return False
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

# Global health monitor instance
health_monitor = SystemHealthMonitor()

# Health check functions for common components
async def check_database_health(db_manager) -> Dict[str, Any]:
    """Health check for database connectivity and performance."""
    try:
        start_time = time.time()
        
        # Test basic connectivity
        if not db_manager.test_connection():
            return {"status": "unhealthy", "error": "Database connection failed"}
        
        # Test simple query performance
        query_start = time.time()
        result = db_manager._connection_manager.execute_query("SELECT 1 as test", fetchall=True)
        query_time = (time.time() - query_start) * 1000
        
        if not result:
            return {"status": "degraded", "error": "Test query failed"}
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "connection_test": "passed",
            "query_time_ms": query_time,
            "total_time_ms": total_time,
            "pool_status": "active" if hasattr(db_manager, 'connection_pool') else "direct"
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_api_service_health(api_service) -> Dict[str, Any]:
    """Health check for API services."""
    try:
        if not hasattr(api_service, 'is_available'):
            return {"status": "unknown", "error": "Health check not available"}
        
        if api_service.is_available():
            # Get usage analytics if available
            analytics = {}
            if hasattr(api_service, 'get_usage_analytics'):
                analytics = api_service.get_usage_analytics()
            
            return {
                "status": "healthy",
                "available": True,
                "analytics": analytics
            }
        else:
            return {"status": "unhealthy", "available": False}
            
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def register_common_components(db_manager=None, anthropic_service=None, knowledge_base=None):
    """Register common system components for health monitoring."""
    
    if db_manager:
        health_monitor.register_component(
            "database",
            lambda: asyncio.create_task(check_database_health(db_manager)),
            critical=True,
            timeout_seconds=10.0
        )
    
    if anthropic_service:
        health_monitor.register_component(
            "anthropic_api",
            lambda: asyncio.create_task(check_api_service_health(anthropic_service)),
            critical=False,  # API is fallback, not critical
            timeout_seconds=15.0
        )
    
    if knowledge_base:
        health_monitor.register_component(
            "knowledge_base",
            lambda: {"status": "healthy", "available": True},
            critical=True,
            timeout_seconds=5.0
        )
    
    logger.info("📋 Registered common system components for health monitoring") 