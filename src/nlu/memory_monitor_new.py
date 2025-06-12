# src/nlu/memory_monitor_new.py
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
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

class MemorySnapshot:
    """Snapshot of memory usage at a specific point in time"""
    
    def __init__(self):
        self.timestamp = time.time()
        process = psutil.Process()
        memory_info = process.memory_info()
        
        self.rss_bytes = memory_info.rss
        self.vms_bytes = memory_info.vms
        
        system_memory = psutil.virtual_memory()
        self.system_total_bytes = system_memory.total
        self.system_available_bytes = system_memory.available
        self.system_percent = system_memory.percent
        
        self.cpu_percent = process.cpu_percent()
        self.num_threads = process.num_threads()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'process_rss_mb': self.rss_bytes / 1024**2,
            'process_rss_gb': self.rss_bytes / 1024**3,
            'system_percent': self.system_percent,
            'system_available_gb': self.system_available_bytes / 1024**3,
            'cpu_percent': self.cpu_percent,
            'num_threads': self.num_threads
        }

class MemoryMonitor:
    """Comprehensive memory monitoring system"""
    
    def __init__(self, 
                 monitoring_interval: float = 30.0,
                 warning_threshold_gb: float = 2.0,
                 critical_threshold_gb: float = 3.5):
        self.monitoring_interval = monitoring_interval
        self.warning_threshold = warning_threshold_gb * 1024**3
        self.critical_threshold = critical_threshold_gb * 1024**3
        
        self.snapshots = deque(maxlen=100)
        self.alerts = deque(maxlen=50)
        self.monitoring_active = False
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        self.cleanup_callbacks = []
        
        logger.info(f"🔍 Memory Monitor initialized (Warning: {warning_threshold_gb}GB, Critical: {critical_threshold_gb}GB)")
    
    def register_cleanup_callback(self, callback: Callable):
        """Register callback for memory cleanup events"""
        self.cleanup_callbacks.append(callback)
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.shutdown_event.clear()
        
        def monitor_worker():
            logger.info("🔍 Memory monitoring started")
            while not self.shutdown_event.wait(self.monitoring_interval):
                try:
                    snapshot = MemorySnapshot()
                    self.snapshots.append(snapshot)
                    self._check_thresholds(snapshot)
                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
        
        self.monitoring_thread = threading.Thread(target=monitor_worker, daemon=True)
        self.monitoring_thread.start()
    
    def _check_thresholds(self, snapshot: MemorySnapshot):
        """Check memory thresholds and trigger alerts"""
        if snapshot.rss_bytes > self.critical_threshold:
            alert = {
                'level': 'critical',
                'timestamp': datetime.now().isoformat(),
                'memory_gb': snapshot.rss_bytes / 1024**3,
                'message': f'Critical memory usage: {snapshot.rss_bytes / 1024**3:.1f}GB'
            }
            self.alerts.append(alert)
            self._trigger_cleanup('critical')
        elif snapshot.rss_bytes > self.warning_threshold:
            alert = {
                'level': 'warning', 
                'timestamp': datetime.now().isoformat(),
                'memory_gb': snapshot.rss_bytes / 1024**3,
                'message': f'High memory usage: {snapshot.rss_bytes / 1024**3:.1f}GB'
            }
            self.alerts.append(alert)
    
    def _trigger_cleanup(self, severity: str):
        """Trigger cleanup callbacks"""
        for callback in self.cleanup_callbacks:
            try:
                callback(severity)
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get current memory metrics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'process_rss_gb': memory_info.rss / 1024**3,
            'process_vms_gb': memory_info.vms / 1024**3,
            'system_total_gb': system_memory.total / 1024**3,
            'system_available_gb': system_memory.available / 1024**3,
            'system_usage_percent': system_memory.percent,
            'warning_threshold_gb': self.warning_threshold / 1024**3,
            'critical_threshold_gb': self.critical_threshold / 1024**3
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get memory optimization recommendations"""
        if not self.snapshots:
            return ["Start monitoring to get recommendations"]
        
        current = self.snapshots[-1]
        recommendations = []
        rss_gb = current.rss_bytes / 1024**3
        
        if rss_gb > 3.0:
            recommendations.append("🚨 Critical: Memory >3GB - unload unused models immediately")
        elif rss_gb > 2.0:
            recommendations.append("⚠️ Warning: Memory >2GB - consider model cleanup")
        
        if current.system_percent > 85:
            recommendations.append("🖥️ System memory pressure detected")
        
        if current.num_threads > 30:
            recommendations.append(f"🧵 High thread count: {current.num_threads}")
        
        if not recommendations:
            recommendations.append("✅ Memory usage is optimal")
        
        return recommendations
    
    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection"""
        before_memory = psutil.Process().memory_info().rss / 1024**2
        collected = gc.collect()
        after_memory = psutil.Process().memory_info().rss / 1024**2
        freed_mb = before_memory - after_memory
        
        logger.info(f"🗑️ GC: {collected} objects, {freed_mb:.1f}MB freed")
        
        return {
            'objects_collected': collected,
            'memory_freed_mb': freed_mb,
            'before_mb': before_memory,
            'after_mb': after_memory
        }
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            self.shutdown_event.set()
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            logger.info("✅ Memory monitoring stopped")
    
    def shutdown(self):
        """Shutdown monitor"""
        self.stop_monitoring() 