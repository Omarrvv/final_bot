from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# ============================================================================
# HEALTH CHECK SCHEMAS
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Basic health check response"""
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime: float = Field(..., description="System uptime in seconds")

class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime: float = Field(..., description="System uptime in seconds")
    components: Dict[str, Any] = Field(..., description="Component health status")
    system_info: Dict[str, Any] = Field(..., description="System information")

class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response"""
    status: str = Field(..., description="Performance status")
    metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    thresholds: Dict[str, float] = Field(..., description="Performance thresholds")
    recommendations: List[str] = Field(..., description="Performance recommendations")

class ReadinessCheckResponse(BaseModel):
    """Readiness check response"""
    ready: bool = Field(..., description="System readiness status")
    checks: Dict[str, bool] = Field(..., description="Individual readiness checks")
    message: str = Field(..., description="Readiness status message")

class LivenessCheckResponse(BaseModel):
    """Liveness check response"""
    alive: bool = Field(..., description="System liveness status")
    message: str = Field(..., description="Liveness status message")

class RequestMetricsRequest(BaseModel):
    """Request metrics recording schema"""
    response_time_ms: float = Field(..., ge=0, description="Response time in milliseconds")
    success: bool = Field(True, description="Request success status")
    database_used: bool = Field(False, description="Whether database was used")
    api_used: bool = Field(False, description="Whether external API was used")

class HealthAlertsResponse(BaseModel):
    """Health alerts response"""
    alerts: List[Dict[str, Any]] = Field(..., description="Active health alerts")
    alert_count: int = Field(..., description="Number of active alerts")
    last_updated: str = Field(..., description="Last update timestamp") 