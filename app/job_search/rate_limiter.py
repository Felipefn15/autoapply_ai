import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests: int
    time_window: float  # in seconds
    burst_limit: int = 1  # Allow burst of requests
    retry_after: float = 1.0  # Wait time after hitting limit

class IntelligentRateLimiter:
    """Intelligent rate limiter with adaptive delays and burst handling."""
    
    def __init__(self):
        self.rate_limits: Dict[str, RateLimitConfig] = {
            'linkedin': RateLimitConfig(max_requests=10, time_window=60, burst_limit=3),
            'glassdoor': RateLimitConfig(max_requests=15, time_window=60, burst_limit=5),
            'indeed': RateLimitConfig(max_requests=20, time_window=60, burst_limit=8),
            'weworkremotely': RateLimitConfig(max_requests=30, time_window=60, burst_limit=10),
            'remotive': RateLimitConfig(max_requests=25, time_window=60, burst_limit=8),
            'angellist': RateLimitConfig(max_requests=8, time_window=60, burst_limit=2),
            'infojobs': RateLimitConfig(max_requests=12, time_window=60, burst_limit=4),
            'catho': RateLimitConfig(max_requests=10, time_window=60, burst_limit=3),
            'hackernews': RateLimitConfig(max_requests=5, time_window=60, burst_limit=2),
            'default': RateLimitConfig(max_requests=15, time_window=60, burst_limit=5)
        }
        
        # Track request history for each platform
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Adaptive delay tracking
        self.adaptive_delays: Dict[str, float] = defaultdict(lambda: 1.0)
        self.success_rates: Dict[str, float] = defaultdict(lambda: 1.0)
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'average_delay': 0.0,
            'platform_performance': defaultdict(lambda: {'requests': 0, 'successes': 0, 'failures': 0})
        }
    
    def get_rate_limit_config(self, platform: str) -> RateLimitConfig:
        """Get rate limit configuration for a platform."""
        return self.rate_limits.get(platform, self.rate_limits['default'])
    
    async def acquire(self, platform: str) -> bool:
        """Acquire permission to make a request."""
        config = self.get_rate_limit_config(platform)
        current_time = time.time()
        
        # Clean old requests outside the time window
        self._clean_old_requests(platform, current_time, config.time_window)
        
        # Check if we're within rate limits
        if len(self.request_history[platform]) >= config.max_requests:
            # Calculate wait time
            oldest_request = self.request_history[platform][0]
            wait_time = config.time_window - (current_time - oldest_request)
            
            if wait_time > 0:
                logger.info(f"Rate limited for {platform}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.metrics['rate_limited_requests'] += 1
        
        # Record this request
        self.request_history[platform].append(current_time)
        self.metrics['total_requests'] += 1
        self.metrics['platform_performance'][platform]['requests'] += 1
        
        return True
    
    async def adaptive_delay(self, platform: str, success: bool = True) -> float:
        """Calculate adaptive delay based on platform performance."""
        config = self.get_rate_limit_config(platform)
        
        # Update success rate
        platform_metrics = self.metrics['platform_performance'][platform]
        if success:
            platform_metrics['successes'] += 1
        else:
            platform_metrics['failures'] += 1
        
        # Calculate success rate
        total_requests = platform_metrics['requests']
        if total_requests > 0:
            self.success_rates[platform] = platform_metrics['successes'] / total_requests
        
        # Adjust delay based on success rate and platform behavior
        base_delay = config.retry_after
        
        if self.success_rates[platform] < 0.8:  # Low success rate
            # Increase delay to be more conservative
            adaptive_delay = base_delay * (1.5 - self.success_rates[platform])
        elif self.success_rates[platform] > 0.95:  # High success rate
            # Decrease delay to be more aggressive
            adaptive_delay = base_delay * max(0.5, self.success_rates[platform] - 0.5)
        else:
            # Normal delay
            adaptive_delay = base_delay
        
        # Apply burst handling
        if len(self.request_history[platform]) > config.burst_limit:
            burst_penalty = 0.5 * (len(self.request_history[platform]) - config.burst_limit)
            adaptive_delay += burst_penalty
        
        # Ensure minimum delay
        adaptive_delay = max(0.1, adaptive_delay)
        
        # Update adaptive delay for this platform
        self.adaptive_delays[platform] = adaptive_delay
        
        # Apply the delay
        await asyncio.sleep(adaptive_delay)
        
        return adaptive_delay
    
    def _clean_old_requests(self, platform: str, current_time: float, time_window: float):
        """Remove old requests from history."""
        while (self.request_history[platform] and 
               current_time - self.request_history[platform][0] > time_window):
            self.request_history[platform].popleft()
    
    async def batch_request(self, platform: str, requests: List[callable], 
                           max_concurrent: int = 5) -> List[Any]:
        """Execute multiple requests with intelligent batching."""
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_request(request_func):
            async with semaphore:
                await self.acquire(platform)
                try:
                    result = await request_func()
                    await self.adaptive_delay(platform, success=True)
                    return result
                except Exception as e:
                    await self.adaptive_delay(platform, success=False)
                    logger.error(f"Request failed for {platform}: {str(e)}")
                    return None
        
        # Execute requests with controlled concurrency
        tasks = [execute_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        results = [r for r in results if not isinstance(r, Exception)]
        
        return results
    
    def get_platform_stats(self, platform: str) -> Dict:
        """Get performance statistics for a specific platform."""
        platform_metrics = self.metrics['platform_performance'][platform]
        total_requests = platform_metrics['requests']
        
        if total_requests == 0:
            return {
                'platform': platform,
                'requests': 0,
                'success_rate': 0.0,
                'average_delay': self.adaptive_delays[platform],
                'current_queue': len(self.request_history[platform])
            }
        
        success_rate = platform_metrics['successes'] / total_requests
        failure_rate = platform_metrics['failures'] / total_requests
        
        return {
            'platform': platform,
            'requests': total_requests,
            'success_rate': round(success_rate * 100, 2),
            'failure_rate': round(failure_rate * 100, 2),
            'average_delay': round(self.adaptive_delays[platform], 2),
            'current_queue': len(self.request_history[platform]),
            'rate_limit_config': {
                'max_requests': self.get_rate_limit_config(platform).max_requests,
                'time_window': self.get_rate_limit_config(platform).time_window,
                'burst_limit': self.get_rate_limit_config(platform).burst_limit
            }
        }
    
    def get_overall_stats(self) -> Dict:
        """Get overall rate limiter statistics."""
        total_requests = self.metrics['total_requests']
        rate_limited = self.metrics['rate_limited_requests']
        
        return {
            'total_requests': total_requests,
            'rate_limited_requests': rate_limited,
            'rate_limit_percentage': round((rate_limited / max(1, total_requests)) * 100, 2),
            'platforms': len(self.rate_limits),
            'average_delay': round(sum(self.adaptive_delays.values()) / len(self.adaptive_delays), 2),
            'platform_performance': {
                platform: self.get_platform_stats(platform)
                for platform in self.rate_limits.keys()
            }
        }
    
    def optimize_for_platform(self, platform: str, performance_data: Dict):
        """Optimize rate limiting for a specific platform based on performance data."""
        try:
            success_rate = performance_data.get('success_rate', 100) / 100
            avg_response_time = performance_data.get('avg_response_time', 1.0)
            
            config = self.get_rate_limit_config(platform)
            
            # Adjust based on success rate
            if success_rate < 0.7:  # Poor performance
                config.max_requests = max(5, config.max_requests - 2)
                config.retry_after = min(5.0, config.retry_after * 1.5)
                logger.info(f"Optimized {platform}: Reduced rate limit due to poor performance")
            elif success_rate > 0.95:  # Excellent performance
                config.max_requests = min(50, config.max_requests + 2)
                config.retry_after = max(0.5, config.retry_after * 0.8)
                logger.info(f"Optimized {platform}: Increased rate limit due to excellent performance")
            
            # Adjust based on response time
            if avg_response_time > 3.0:  # Slow responses
                config.retry_after = min(3.0, config.retry_after * 1.2)
            elif avg_response_time < 0.5:  # Fast responses
                config.retry_after = max(0.3, config.retry_after * 0.9)
                
        except Exception as e:
            logger.error(f"Error optimizing rate limits for {platform}: {str(e)}")
    
    def reset_platform(self, platform: str):
        """Reset rate limiting for a specific platform."""
        if platform in self.request_history:
            self.request_history[platform].clear()
        if platform in self.adaptive_delays:
            self.adaptive_delays[platform] = 1.0
        if platform in self.success_rates:
            self.success_rates[platform] = 1.0
        
        logger.info(f"Reset rate limiting for {platform}")
    
    def get_status_report(self) -> str:
        """Get a human-readable status report."""
        overall_stats = self.get_overall_stats()
        
        report = f"""
🚀 RATE LIMITER STATUS REPORT
============================
📊 Overall Performance:
   Total Requests: {overall_stats['total_requests']}
   Rate Limited: {overall_stats['rate_limited_requests']} ({overall_stats['rate_limit_percentage']}%)
   Average Delay: {overall_stats['average_delay']}s

🌐 Platform Performance:
"""
        
        for platform, stats in overall_stats['platform_performance'].items():
            report += f"""
   {platform.upper()}:
      Requests: {stats['requests']}
      Success Rate: {stats['success_rate']}%
      Current Queue: {stats['current_queue']}
      Average Delay: {stats['average_delay']}s
"""
        
        return report
