"""
Rate-Limited Anthropic Service

Provides cost-controlled, timeout-aware wrapper around the Anthropic API service.
Prevents cost explosion and implements graceful degradation for production reliability.
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.error_handler import UnifiedErrorHandler, reliability_tracker

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Raised when API rate limits are exceeded."""
    pass

class CostLimitError(Exception):
    """Raised when cost limits are exceeded."""
    pass

class RateLimitedAnthropicService:
    """
    Rate-limited wrapper around Anthropic service for production reliability.
    
    Features:
    - Hourly and daily rate limiting
    - Cost monitoring and limits
    - Timeout handling with retries
    - Graceful degradation
    - Usage analytics
    """
    
    def __init__(self, anthropic_service, config: Optional[Dict[str, Any]] = None):
        """
        Initialize rate-limited service.
        
        Args:
            anthropic_service: The underlying Anthropic service
            config: Configuration for rate limits and costs
        """
        self.anthropic_service = anthropic_service
        
        # Default configuration
        default_config = {
            'max_calls_per_hour': 100,
            'max_calls_per_day': 1000,
            'daily_cost_limit_usd': 50.0,
            'estimated_cost_per_call': 0.01,
            'timeout_seconds': 30.0,
            'max_retries': 3,
            'enable_cost_tracking': True,
            'enable_rate_limiting': True
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Tracking data structures
        self.call_timestamps = defaultdict(list)
        self.cost_tracking = {
            'daily_cost': 0.0,
            'daily_calls': 0,
            'last_reset': datetime.now().date(),
            'total_cost': 0.0,
            'total_calls': 0
        }
        
        # Performance metrics
        self.performance_metrics = {
            'successful_calls': 0,
            'failed_calls': 0,
            'timeout_calls': 0,
            'rate_limited_calls': 0,
            'cost_limited_calls': 0,
            'average_response_time': 0.0,
            'total_response_time': 0.0
        }
        
        logger.info(f"✅ Initialized Rate-Limited Anthropic Service with config: {self.config}")
    
    def _reset_daily_tracking_if_needed(self):
        """Reset daily tracking if it's a new day."""
        today = datetime.now().date()
        if self.cost_tracking['last_reset'] != today:
            logger.info(f"🔄 Resetting daily tracking for new day: {today}")
            self.cost_tracking['daily_cost'] = 0.0
            self.cost_tracking['daily_calls'] = 0
            self.cost_tracking['last_reset'] = today
            
            # Clean old timestamps (keep only last 24 hours)
            cutoff_time = time.time() - 86400  # 24 hours ago
            for key in self.call_timestamps:
                self.call_timestamps[key] = [
                    t for t in self.call_timestamps[key] if t > cutoff_time
                ]
    
    def _check_rate_limits(self):
        """
        Check if API call is within rate limits.
        
        Raises:
            RateLimitError: If rate limits are exceeded
            CostLimitError: If cost limits are exceeded
        """
        if not self.config['enable_rate_limiting']:
            return
            
        now = time.time()
        hour_ago = now - 3600  # 1 hour ago
        day_ago = now - 86400   # 24 hours ago
        
        # Clean old timestamps
        recent_calls = [t for t in self.call_timestamps['api_calls'] if t > hour_ago]
        daily_calls = [t for t in self.call_timestamps['api_calls'] if t > day_ago]
        
        # Check hourly rate limit
        if len(recent_calls) >= self.config['max_calls_per_hour']:
            self.performance_metrics['rate_limited_calls'] += 1
            reliability_tracker.log_error("rate_limit", "anthropic", f"Hourly limit: {len(recent_calls)}")
            raise RateLimitError(
                f"Hourly rate limit exceeded: {len(recent_calls)}/{self.config['max_calls_per_hour']} calls/hour"
            )
        
        # Check daily rate limit
        if len(daily_calls) >= self.config['max_calls_per_day']:
            self.performance_metrics['rate_limited_calls'] += 1
            reliability_tracker.log_error("rate_limit", "anthropic", f"Daily limit: {len(daily_calls)}")
            raise RateLimitError(
                f"Daily rate limit exceeded: {len(daily_calls)}/{self.config['max_calls_per_day']} calls/day"
            )
        
        # Check cost limits if enabled
        if self.config['enable_cost_tracking']:
            self._reset_daily_tracking_if_needed()
            
            estimated_new_cost = self.cost_tracking['daily_cost'] + self.config['estimated_cost_per_call']
            if estimated_new_cost > self.config['daily_cost_limit_usd']:
                self.performance_metrics['cost_limited_calls'] += 1
                reliability_tracker.log_error("cost_limit", "anthropic", f"Daily cost: ${estimated_new_cost:.2f}")
                raise CostLimitError(
                    f"Daily cost limit exceeded: ${estimated_new_cost:.2f}/${self.config['daily_cost_limit_usd']:.2f}"
                )
    
    def _log_api_call(self, success: bool, response_time: float, cost: float = None):
        """Log API call for tracking and analytics."""
        now = time.time()
        
        # Log timestamp
        self.call_timestamps['api_calls'].append(now)
        
        # Update performance metrics
        if success:
            self.performance_metrics['successful_calls'] += 1
            reliability_tracker.log_recovery("api_call", "anthropic")
        else:
            self.performance_metrics['failed_calls'] += 1
            reliability_tracker.log_error("api_call", "anthropic", "Call failed")
        
        # Update response time tracking
        self.performance_metrics['total_response_time'] += response_time
        total_calls = self.performance_metrics['successful_calls'] + self.performance_metrics['failed_calls']
        if total_calls > 0:
            self.performance_metrics['average_response_time'] = (
                self.performance_metrics['total_response_time'] / total_calls
            )
        
        # Update cost tracking
        if self.config['enable_cost_tracking']:
            self._reset_daily_tracking_if_needed()
            call_cost = cost or self.config['estimated_cost_per_call']
            
            self.cost_tracking['daily_cost'] += call_cost
            self.cost_tracking['daily_calls'] += 1
            self.cost_tracking['total_cost'] += call_cost
            self.cost_tracking['total_calls'] += 1
    
    async def generate_response_safe(self, prompt: str, max_tokens: int = 300, 
                                   language: str = "en", **kwargs) -> Dict[str, Any]:
        """
        Generate API response with rate limiting, timeout handling, and fallbacks.
        
        Args:
            prompt: The prompt to send to the API
            max_tokens: Maximum tokens in response
            language: Language for error messages
            **kwargs: Additional arguments for the API call
            
        Returns:
            API response or graceful error response
        """
        start_time = time.time()
        
        try:
            # Check rate and cost limits
            self._check_rate_limits()
            
            # Implement timeout with retries
            for attempt in range(self.config['max_retries']):
                try:
                    logger.debug(f"🤖 Anthropic API call attempt {attempt + 1}/{self.config['max_retries']}")
                    
                    # Make the API call with timeout
                    response = await asyncio.wait_for(
                        self._make_api_call(prompt, max_tokens, **kwargs),
                        timeout=self.config['timeout_seconds']
                    )
                    
                    # Log successful call
                    response_time = time.time() - start_time
                    self._log_api_call(True, response_time)
                    
                    logger.debug(f"✅ Anthropic API call successful in {response_time:.2f}s")
                    
                    return {
                        "text": response,
                        "response_type": "api_response",
                        "source": "anthropic_rate_limited",
                        "language": language,
                        "response_time": response_time,
                        "attempt": attempt + 1,
                        "fallback": False
                    }
                    
                except asyncio.TimeoutError:
                    self.performance_metrics['timeout_calls'] += 1
                    logger.warning(f"⏰ Anthropic API timeout on attempt {attempt + 1}")
                    
                    if attempt < self.config['max_retries'] - 1:
                        # Exponential backoff before retry
                        wait_time = (2 ** attempt) * 0.5
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Final timeout
                        response_time = time.time() - start_time
                        self._log_api_call(False, response_time)
                        
                        return UnifiedErrorHandler.handle_timeout_error(
                            "anthropic_api_call", self.config['timeout_seconds'], 
                            "anthropic", language
                        )
                
                except Exception as e:
                    logger.warning(f"❌ Anthropic API error on attempt {attempt + 1}: {str(e)}")
                    
                    if attempt < self.config['max_retries'] - 1:
                        # Wait before retry
                        wait_time = (2 ** attempt) * 0.5
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Final error
                        response_time = time.time() - start_time
                        self._log_api_call(False, response_time)
                        
                        return UnifiedErrorHandler.handle_api_error(
                            "anthropic", e, "generate_response", language
                        )
        
        except RateLimitError as e:
            logger.warning(f"🚫 Rate limit exceeded: {str(e)}")
            return UnifiedErrorHandler.handle_api_error(
                "anthropic", e, "rate_check", language
            )
        
        except CostLimitError as e:
            logger.warning(f"💰 Cost limit exceeded: {str(e)}")
            return UnifiedErrorHandler.handle_api_error(
                "anthropic", e, "cost_check", language
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            self._log_api_call(False, response_time)
            
            logger.error(f"🔥 Unexpected error in rate-limited service: {str(e)}")
            return UnifiedErrorHandler.handle_api_error(
                "anthropic", e, "unexpected_error", language
            )
    
    async def _make_api_call(self, prompt: str, max_tokens: int, **kwargs) -> str:
        """
        Make the actual API call to Anthropic.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            **kwargs: Additional API parameters
            
        Returns:
            Response text from API
        """
        # Call the underlying Anthropic service
        if hasattr(self.anthropic_service, 'generate_response'):
            # Synchronous method
            return self.anthropic_service.generate_response(
                prompt=prompt, max_tokens=max_tokens, **kwargs
            )
        elif hasattr(self.anthropic_service, 'generate_response_async'):
            # Asynchronous method
            return await self.anthropic_service.generate_response_async(
                prompt=prompt, max_tokens=max_tokens, **kwargs
            )
        else:
            raise AttributeError("Anthropic service missing generate_response method")
    
    def get_usage_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive usage analytics and cost tracking.
        
        Returns:
            Dictionary with usage statistics and cost information
        """
        self._reset_daily_tracking_if_needed()
        
        now = time.time()
        hour_ago = now - 3600
        recent_calls = [t for t in self.call_timestamps['api_calls'] if t > hour_ago]
        
        return {
            "rate_limits": {
                "calls_this_hour": len(recent_calls),
                "hourly_limit": self.config['max_calls_per_hour'],
                "calls_today": self.cost_tracking['daily_calls'],
                "daily_limit": self.config['max_calls_per_day'],
                "rate_limit_usage_percent": (len(recent_calls) / self.config['max_calls_per_hour']) * 100
            },
            "cost_tracking": {
                "daily_cost": self.cost_tracking['daily_cost'],
                "daily_limit": self.config['daily_cost_limit_usd'],
                "cost_usage_percent": (self.cost_tracking['daily_cost'] / self.config['daily_cost_limit_usd']) * 100,
                "total_cost": self.cost_tracking['total_cost'],
                "total_calls": self.cost_tracking['total_calls'],
                "average_cost_per_call": (
                    self.cost_tracking['total_cost'] / max(self.cost_tracking['total_calls'], 1)
                )
            },
            "performance": {
                "successful_calls": self.performance_metrics['successful_calls'],
                "failed_calls": self.performance_metrics['failed_calls'],
                "timeout_calls": self.performance_metrics['timeout_calls'],
                "rate_limited_calls": self.performance_metrics['rate_limited_calls'],
                "cost_limited_calls": self.performance_metrics['cost_limited_calls'],
                "success_rate": (
                    self.performance_metrics['successful_calls'] / 
                    max(self.performance_metrics['successful_calls'] + self.performance_metrics['failed_calls'], 1)
                ) * 100,
                "average_response_time": self.performance_metrics['average_response_time']
            },
            "configuration": {
                "rate_limiting_enabled": self.config['enable_rate_limiting'],
                "cost_tracking_enabled": self.config['enable_cost_tracking'],
                "timeout_seconds": self.config['timeout_seconds'],
                "max_retries": self.config['max_retries']
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_tracking(self):
        """Reset all tracking data (for testing or manual reset)."""
        self.call_timestamps.clear()
        self.cost_tracking = {
            'daily_cost': 0.0,
            'daily_calls': 0,
            'last_reset': datetime.now().date(),
            'total_cost': 0.0,
            'total_calls': 0
        }
        self.performance_metrics = {
            'successful_calls': 0,
            'failed_calls': 0,
            'timeout_calls': 0,
            'rate_limited_calls': 0,
            'cost_limited_calls': 0,
            'average_response_time': 0.0,
            'total_response_time': 0.0
        }
        logger.info("🔄 Reset all tracking data")
    
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy and operating within limits.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            analytics = self.get_usage_analytics()
            
            # Check if we're within reasonable limits
            rate_usage = analytics['rate_limits']['rate_limit_usage_percent']
            cost_usage = analytics['cost_tracking']['cost_usage_percent']
            success_rate = analytics['performance']['success_rate']
            
            # Consider unhealthy if:
            # - Using more than 90% of rate limits
            # - Using more than 95% of cost limits  
            # - Success rate below 80%
            if rate_usage > 90:
                logger.warning(f"🚨 High rate limit usage: {rate_usage:.1f}%")
                return False
            
            if cost_usage > 95:
                logger.warning(f"🚨 High cost usage: {cost_usage:.1f}%")
                return False
            
            if success_rate < 80:
                logger.warning(f"🚨 Low success rate: {success_rate:.1f}%")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking service health: {str(e)}")
            return False 