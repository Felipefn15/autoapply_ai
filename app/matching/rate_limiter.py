import time
from typing import Optional
from loguru import logger

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 50, buffer_percent: int = 20):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum number of calls allowed per minute
            buffer_percent: Percentage buffer to stay under the limit (0-100)
        """
        self.calls_per_minute = calls_per_minute
        self.buffer_percent = max(0, min(100, buffer_percent))
        self.effective_rate = calls_per_minute * (1 - buffer_percent/100)
        self.call_timestamps = []
        self.last_warning_time = 0
        self.warning_interval = 60  # Only warn once per minute
        
    def wait_if_needed(self) -> None:
        """Wait if necessary to stay within rate limits."""
        now = time.time()
        
        # Remove timestamps older than 1 minute
        self.call_timestamps = [ts for ts in self.call_timestamps if now - ts < 60]
        
        # Calculate current rate
        current_calls = len(self.call_timestamps)
        
        if current_calls >= 10:
            # Log every 10 calls
            logger.info(f"Processed {current_calls} API calls")
        
        if current_calls >= self.effective_rate:
            # Calculate required wait time
            oldest_timestamp = self.call_timestamps[0]
            wait_time = 60 - (now - oldest_timestamp)
            
            if wait_time > 0:
                # Only log warning if enough time has passed since last warning
                if now - self.last_warning_time >= self.warning_interval:
                    logger.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                    self.last_warning_time = now
                
                time.sleep(wait_time)
        
        # Add current timestamp
        self.call_timestamps.append(time.time())
        
    def get_current_rate(self) -> float:
        """Get current calls per minute rate."""
        now = time.time()
        recent_calls = [ts for ts in self.call_timestamps if now - ts < 60]
        return len(recent_calls) 