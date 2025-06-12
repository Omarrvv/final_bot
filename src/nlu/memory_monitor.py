# src/nlu/memory_monitor.py
"""
Memory Monitor for Egypt Tourism Chatbot NLU Engine.

This module provides comprehensive memory monitoring with:
- Real-time memory usage tracking
- Automatic cleanup triggers
- Memory leak detection
- Performance alerts
- AI-powered optimization recommendations

Phase 4: Memory & Caching Optimization
"""
import gc
import logging
import psutil
import threading
import time
import tracemalloc
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class MemorySnapshot:
    """Snapshot of memory usage at a specific point in time"""
    
    def __init__(self):
        self.timestamp = time.time()
        self.process = psutil.Process()
        
        # Process memory info
        memory_info = self.process.memory_info()
        self.rss_bytes = memory_info.rss  # Resident Set Size
        self.vms_bytes = memory_info.vms  # Virtual Memory Size
        
        # System memory info
        system_memory = psutil.virtual_memory()
        self.system_total_bytes = system_memory.total
        self.system_available_bytes = system_memory.available
        self.system_percent = system_memory.percent
        
        # Additional process metrics
        self.cpu_percent = self.process.cpu_percent()
        self.num_threads = self.process.num_threads()
        self.num_fds = getattr(self.process, 'num_fds', lambda: 0)()  # Unix only
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary"""
        return {
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'timestamp_unix': self.timestamp,
            'process_rss_mb': self.rss_bytes / 1024**2,
            'process_vms_mb': self.vms_bytes / 1024**2,
            'process_rss_gb': self.rss_bytes / 1024**3,
            'process_vms_gb': self.vms_bytes / 1024**3,
            'system_total_gb': self.system_total_bytes / 1024**3,
            'system_available_gb': self.system_available_bytes / 1024**3,
            'system_percent': self.system_percent,
            'cpu_percent': self.cpu_percent,
            'num_threads': self.num_threads,
            'num_fds': self.num_fds
        }

class MemoryLeakDetector:
    """Detect potential memory leaks using statistical analysis"""
    
    def __init__(self, history_size: int = 100, growth_threshold: float = 0.05):
        self.history_size = history_size
        self.growth_threshold = growth_threshold  # 5% growth over window
        self.snapshots = deque(maxlen=history_size)
        
    def add_snapshot(self, snapshot: MemorySnapshot):
        """Add a memory snapshot for analysis"""
        self.snapshots.append(snapshot)
    
    def detect_leaks(self) -> Dict[str, Any]:
        """Detect memory leaks using trend analysis"""
        if len(self.snapshots) < 10:  # Need minimum data
            return {'leak_detected': False, 'reason': 'Insufficient data'}
        
        # Convert to numpy arrays for analysis
        timestamps = np.array([s.timestamp for s in self.snapshots])
        rss_mb = np.array([s.rss_bytes / 1024**2 for s in self.snapshots])
        
        # Calculate trend using linear regression
        time_relative = timestamps - timestamps[0]
        coeffs = np.polyfit(time_relative, rss_mb, 1)
        slope = coeffs[0]  # MB per second
        
        # Calculate growth rate over entire window
        time_span_hours = (timestamps[-1] - timestamps[0]) / 3600
        total_growth_mb = rss_mb[-1] - rss_mb[0]
        growth_rate_mb_per_hour = total_growth_mb / max(time_span_hours, 0.01)
        
        # Detect leak based on consistent growth
        leak_detected = False
        leak_severity = 'none'
        
        if slope > 0.1 and growth_rate_mb_per_hour > 10:  # 10MB/hour growth
            leak_detected = True
            if growth_rate_mb_per_hour > 100:
                leak_severity = 'critical'
            elif growth_rate_mb_per_hour > 50:
                leak_severity = 'high'
            else:
                leak_severity = 'moderate'
        
        return {
            'leak_detected': leak_detected,
            'leak_severity': leak_severity,
            'slope_mb_per_second': slope,
            'growth_rate_mb_per_hour': growth_rate_mb_per_hour,
            'total_growth_mb': total_growth_mb,
            'time_span_hours': time_span_hours,
            'current_rss_mb': rss_mb[-1],
            'min_rss_mb': np.min(rss_mb),
            'max_rss_mb': np.max(rss_mb),
            'avg_rss_mb': np.mean(rss_mb),
            'std_rss_mb': np.std(rss_mb)
        }

class MemoryAlert:
    """Memory alert system with different severity levels"""
    
    def __init__(self):
        self.alerts = []
        self.alert_history = deque(maxlen=100)
        
    def check_alerts(self, snapshot: MemorySnapshot) -> List[Dict[str, Any]]:
        """Check for memory-related alerts"""
        alerts = []
        
        # Convert to GB for readability
        rss_gb = snapshot.rss_bytes / 1024**3
        system_percent = snapshot.system_percent
        available_gb = snapshot.system_available_bytes / 1024**3
        
        # Critical memory usage (>4GB)
        if rss_gb > 4.0:
            alerts.append({
                'level': 'critical',
                'type': 'high_memory_usage',
                'message': f'Process memory usage is critical: {rss_gb:.1f}GB',
                'value': rss_gb,
                'threshold': 4.0,
                'recommendation': 'Immediate cleanup required - consider restarting models'
            })
        
        # High memory usage (>2.5GB)
        elif rss_gb > 2.5:
            alerts.append({
                'level': 'warning',
                'type': 'high_memory_usage',
                'message': f'Process memory usage is high: {rss_gb:.1f}GB',
                'value': rss_gb,
                'threshold': 2.5,
                'recommendation': 'Consider unloading unused models'
            })
        
        # System memory pressure (>85%)
        if system_percent > 85:
            alerts.append({
                'level': 'critical' if system_percent > 95 else 'warning',
                'type': 'system_memory_pressure',
                'message': f'System memory usage is {system_percent:.1f}%',
                'value': system_percent,
                'threshold': 85,
                'recommendation': 'System-wide memory pressure detected'
            })
        
        # Low available memory (<500MB)
        if available_gb < 0.5:
            alerts.append({
                'level': 'critical',
                'type': 'low_available_memory',
                'message': f'Low available system memory: {available_gb:.1f}GB',
                'value': available_gb,
                'threshold': 0.5,
                'recommendation': 'Free memory immediately'
            })
        
        # High thread count
        if snapshot.num_threads > 50:
            alerts.append({
                'level': 'warning',
                'type': 'high_thread_count',
                'message': f'High thread count: {snapshot.num_threads}',
                'value': snapshot.num_threads,
                'threshold': 50,
                'recommendation': 'Monitor for thread leaks'
            })
        
        # Store alerts with timestamp
        for alert in alerts:
            alert['timestamp'] = datetime.fromtimestamp(snapshot.timestamp).isoformat()
            self.alert_history.append(alert)
        
        return alerts

class MemoryOptimizer:
    """Provide AI-powered memory optimization recommendations"""
    
    def __init__(self):
        self.optimization_history = deque(maxlen=50)
        
    def analyze_and_recommend(self, 
                            current_snapshot: MemorySnapshot,
                            leak_analysis: Dict[str, Any],
                            recent_snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """Analyze memory patterns and provide optimization recommendations"""
        
        recommendations = []
        actions = []
        priority_score = 0
        
        rss_gb = current_snapshot.rss_bytes / 1024**3
        system_percent = current_snapshot.system_percent
        
        # Immediate actions for critical situations
        if rss_gb > 4.0 or system_percent > 90:
            priority_score = 10
            recommendations.append({
                'priority': 'critical',
                'action': 'immediate_cleanup',
                'description': 'Immediate memory cleanup required',
                'commands': ['gc.collect()', 'unload_unused_models()', 'clear_caches()']
            })
            actions.append('Trigger emergency memory cleanup')
        
        # Model management recommendations
        if rss_gb > 2.0:
            priority_score = max(priority_score, 8)
            recommendations.append({
                'priority': 'high',
                'action': 'model_optimization',
                'description': 'Optimize model memory usage',
                'commands': ['unload_rarely_used_models()', 'enable_model_sharing()']
            })
        
        # Cache optimization
        if len(recent_snapshots) > 5:
            memory_trend = np.mean([s.rss_bytes for s in recent_snapshots[-5:]])
            if memory_trend > np.mean([s.rss_bytes for s in recent_snapshots[:5]]):
                priority_score = max(priority_score, 6)
                recommendations.append({
                    'priority': 'medium',
                    'action': 'cache_optimization',
                    'description': 'Optimize cache settings',
                    'commands': ['reduce_cache_sizes()', 'enable_cache_compression()']
                })
        
        # Memory leak handling
        if leak_analysis.get('leak_detected', False):
            severity = leak_analysis.get('leak_severity', 'unknown')
            if severity == 'critical':
                priority_score = 10
                recommendations.append({
                    'priority': 'critical',
                    'action': 'leak_mitigation',
                    'description': f'Critical memory leak detected ({leak_analysis.get("growth_rate_mb_per_hour", 0):.1f}MB/hour)',
                    'commands': ['investigate_leak_sources()', 'restart_leaking_components()']
                })
            elif severity in ['high', 'moderate']:
                priority_score = max(priority_score, 7)
                recommendations.append({
                    'priority': 'high',
                    'action': 'leak_monitoring',
                    'description': f'Memory leak detected ({leak_analysis.get("growth_rate_mb_per_hour", 0):.1f}MB/hour)',
                    'commands': ['enable_detailed_tracking()', 'monitor_allocation_patterns()']
                })
        
        # Proactive optimizations
        if rss_gb > 1.5 and priority_score < 5:
            recommendations.append({
                'priority': 'low',
                'action': 'proactive_optimization',
                'description': 'Proactive memory optimization',
                'commands': ['optimize_data_structures()', 'enable_lazy_loading()']
            })
        
        return {
            'timestamp': datetime.fromtimestamp(current_snapshot.timestamp).isoformat(),
            'priority_score': priority_score,
            'current_memory_gb': rss_gb,
            'system_memory_percent': system_percent,
            'recommendations': recommendations,
            'suggested_actions': actions,
            'analysis': {
                'memory_pressure': 'critical' if rss_gb > 4 else 'high' if rss_gb > 2 else 'normal',
                'leak_status': leak_analysis.get('leak_severity', 'none'),
                'optimization_needed': len(recommendations) > 0
            }
        }

class MemoryMonitor:
    """
    Comprehensive memory monitoring system.
    
    Features:
    - Real-time memory usage tracking
    - Memory leak detection
    - Performance alerts
    - Optimization recommendations
    - Automatic cleanup triggers
    """
    
    def __init__(self, 
                 monitoring_interval: float = 30.0,
                 history_size: int = 1000,
                 warning_threshold_gb: float = 2.0,
                 critical_threshold_gb: float = 3.5,
                 enable_tracemalloc: bool = False):
        """
        Initialize Memory Monitor.
        
        Args:
            monitoring_interval: Seconds between memory snapshots
            history_size: Number of snapshots to keep in memory
            warning_threshold_gb: Memory usage threshold for warnings
            critical_threshold_gb: Memory usage threshold for critical alerts
            enable_tracemalloc: Enable detailed Python memory tracking
        """
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        self.warning_threshold = warning_threshold_gb * 1024**3
        self.critical_threshold = critical_threshold_gb * 1024**3
        self.enable_tracemalloc = enable_tracemalloc
        
        # Data storage
        self.snapshots = deque(maxlen=history_size)
        self.alerts = deque(maxlen=100)
        
        # Components
        self.leak_detector = MemoryLeakDetector()
        self.alert_system = MemoryAlert()
        self.optimizer = MemoryOptimizer()
        
        # Monitoring control
        self.monitoring_active = False
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        
        # Callbacks for memory events
        self.cleanup_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # Initialize tracemalloc if requested
        if self.enable_tracemalloc:
            tracemalloc.start()
        
        logger.info(f"🔍 Memory Monitor initialized:")
        logger.info(f"   Monitoring interval: {monitoring_interval}s")
        logger.info(f"   Warning threshold: {warning_threshold_gb}GB")
        logger.info(f"   Critical threshold: {critical_threshold_gb}GB")
        logger.info(f"   Tracemalloc enabled: {enable_tracemalloc}")
    
    def register_cleanup_callback(self, callback: Callable):
        """Register a callback for memory cleanup events"""
        self.cleanup_callbacks.append(callback)
        logger.debug(f"Registered cleanup callback: {callback.__name__}")
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for memory alerts"""
        self.alert_callbacks.append(callback)
        logger.debug(f"Registered alert callback: {callback.__name__}")
    
    def start_monitoring(self):
        """Start background memory monitoring"""
        if self.monitoring_active:
            logger.warning("Memory monitoring already active")
            return
        
        self.monitoring_active = True
        self.shutdown_event.clear()
        
        def monitor_worker():
            logger.info("🔍 Memory monitoring started")
            while not self.shutdown_event.wait(self.monitoring_interval):
                try:
                    self._take_snapshot_and_analyze()
                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
        
        self.monitoring_thread = threading.Thread(target=monitor_worker, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background memory monitoring"""
        if not self.monitoring_active:
            return
        
        logger.info("🔍 Stopping memory monitoring...")
        self.monitoring_active = False
        self.shutdown_event.set()
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        logger.info("✅ Memory monitoring stopped")
    
    def _take_snapshot_and_analyze(self):
        """Take a memory snapshot and perform analysis"""
        # Take snapshot
        snapshot = MemorySnapshot()
        self.snapshots.append(snapshot)
        self.leak_detector.add_snapshot(snapshot)
        
        # Check for alerts
        alerts = self.alert_system.check_alerts(snapshot)
        for alert in alerts:
            self.alerts.append(alert)
            
            # Trigger alert callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
        
        # Trigger cleanup if thresholds exceeded
        if snapshot.rss_bytes > self.critical_threshold:
            logger.warning(f"🚨 Critical memory threshold exceeded: {snapshot.rss_bytes / 1024**3:.1f}GB")
            self._trigger_cleanup('critical')
        elif snapshot.rss_bytes > self.warning_threshold:
            logger.warning(f"⚠️ Memory warning threshold exceeded: {snapshot.rss_bytes / 1024**3:.1f}GB")
            self._trigger_cleanup('warning')
    
    def _trigger_cleanup(self, severity: str):
        """Trigger memory cleanup callbacks"""
        for callback in self.cleanup_callbacks:
            try:
                callback(severity)
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current memory metrics"""
        if not self.snapshots:
            return {'error': 'No snapshots available'}
        
        current = self.snapshots[-1]
        return current.to_dict()
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive memory analysis with recommendations"""
        if len(self.snapshots) < 2:
            return {'error': 'Insufficient data for analysis'}
        
        current_snapshot = self.snapshots[-1]
        recent_snapshots = list(self.snapshots)[-20:]  # Last 20 snapshots
        
        # Perform leak detection
        leak_analysis = self.leak_detector.detect_leaks()
        
        # Get optimization recommendations
        optimization_analysis = self.optimizer.analyze_and_recommend(
            current_snapshot, leak_analysis, recent_snapshots
        )
        
        # Calculate trends
        if len(recent_snapshots) >= 5:
            memory_values = [s.rss_bytes / 1024**3 for s in recent_snapshots]
            memory_trend = 'increasing' if memory_values[-1] > memory_values[0] else 'decreasing'
            memory_volatility = np.std(memory_values)
        else:
            memory_trend = 'unknown'
            memory_volatility = 0
        
        # Recent alerts
        recent_alerts = [alert for alert in self.alerts if alert.get('timestamp') and 
                        datetime.fromisoformat(alert['timestamp']) > datetime.now() - timedelta(hours=1)]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': current_snapshot.to_dict(),
            'leak_analysis': leak_analysis,
            'optimization_analysis': optimization_analysis,
            'trends': {
                'memory_trend': memory_trend,
                'memory_volatility': memory_volatility,
                'snapshot_count': len(self.snapshots),
                'monitoring_duration_hours': (current_snapshot.timestamp - self.snapshots[0].timestamp) / 3600 if len(self.snapshots) > 1 else 0
            },
            'recent_alerts': recent_alerts,
            'summary': {
                'status': 'critical' if current_snapshot.rss_bytes > self.critical_threshold 
                         else 'warning' if current_snapshot.rss_bytes > self.warning_threshold 
                         else 'normal',
                'memory_gb': current_snapshot.rss_bytes / 1024**3,
                'system_usage_percent': current_snapshot.system_percent,
                'alerts_last_hour': len(recent_alerts),
                'leak_detected': leak_analysis.get('leak_detected', False)
            }
        }
    
    def get_memory_report(self) -> str:
        """Generate a human-readable memory report"""
        analysis = self.get_comprehensive_analysis()
        
        if 'error' in analysis:
            return f"Memory Report: {analysis['error']}"
        
        current = analysis['current_metrics']
        summary = analysis['summary']
        
        report = []
        report.append("🔍 MEMORY MONITOR REPORT")
        report.append("=" * 50)
        report.append(f"Status: {summary['status'].upper()}")
        report.append(f"Memory Usage: {summary['memory_gb']:.1f}GB")
        report.append(f"System Usage: {summary['system_usage_percent']:.1f}%")
        report.append(f"Monitoring: {analysis['trends']['monitoring_duration_hours']:.1f}h")
        report.append("")
        
        # Alerts
        if summary['alerts_last_hour'] > 0:
            report.append(f"⚠️ ALERTS: {summary['alerts_last_hour']} in last hour")
        
        # Leak detection
        if summary['leak_detected']:
            leak_info = analysis['leak_analysis']
            report.append(f"🚨 MEMORY LEAK: {leak_info['leak_severity']} ({leak_info['growth_rate_mb_per_hour']:.1f}MB/hour)")
        
        # Recommendations
        recommendations = analysis['optimization_analysis']['recommendations']
        if recommendations:
            report.append("")
            report.append("💡 RECOMMENDATIONS:")
            for rec in recommendations[:3]:  # Top 3 recommendations
                report.append(f"   {rec['priority'].upper()}: {rec['description']}")
        
        return "\n".join(report)
    
    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return before/after metrics"""
        before = MemorySnapshot()
        
        # Force garbage collection
        collected = gc.collect()
        
        after = MemorySnapshot()
        
        memory_freed_mb = (before.rss_bytes - after.rss_bytes) / 1024**2
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'objects_collected': collected,
            'memory_freed_mb': memory_freed_mb,
            'before_rss_mb': before.rss_bytes / 1024**2,
            'after_rss_mb': after.rss_bytes / 1024**2,
            'effectiveness': 'high' if memory_freed_mb > 50 else 'medium' if memory_freed_mb > 10 else 'low'
        }
        
        logger.info(f"🗑️ Garbage collection: {collected} objects, {memory_freed_mb:.1f}MB freed")
        return result
    
    def shutdown(self):
        """Shutdown the memory monitor"""
        logger.info("🛑 Shutting down Memory Monitor...")
        self.stop_monitoring()
        
        if self.enable_tracemalloc:
            tracemalloc.stop()
        
        logger.info("✅ Memory Monitor shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.shutdown()
        except:
            pass  # Ignore errors during cleanup 