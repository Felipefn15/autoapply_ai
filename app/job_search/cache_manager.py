import json
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class JobCacheManager:
    """Intelligent cache manager for job search results."""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.cache_ttl = 3600  # 1 hour in seconds
        self.max_cache_size = 100 * 1024 * 1024  # 100MB
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _generate_cache_key(self, platform: str, category: str, keywords: List[str]) -> str:
        """Generate a unique cache key for the search."""
        search_string = f"{platform}:{category}:{':'.join(sorted(keywords))}"
        return hashlib.md5(search_string.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"jobs_{cache_key}.json"
    
    def get_cached_jobs(self, platform: str, category: str, keywords: List[str]) -> Optional[List[Dict]]:
        """Get cached jobs if they exist and are still valid."""
        try:
            cache_key = self._generate_cache_key(platform, category, keywords)
            cache_file = self._get_cache_file_path(cache_key)
            
            if not cache_file.exists():
                self.cache_stats['misses'] += 1
                return None
            
            # Check if cache is still valid
            if self._is_cache_expired(cache_file):
                logger.info(f"Cache expired for {platform}:{category}")
                cache_file.unlink()  # Remove expired cache
                self.cache_stats['misses'] += 1
                return None
            
            # Load cached data
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            self.cache_stats['hits'] += 1
            logger.info(f"Cache hit for {platform}:{category} - {len(cached_data.get('jobs', []))} jobs")
            return cached_data.get('jobs', [])
            
        except Exception as e:
            logger.error(f"Error reading cache: {str(e)}")
            self.cache_stats['misses'] += 1
            return None
    
    def cache_jobs(self, platform: str, category: str, keywords: List[str], jobs: List[Dict]) -> bool:
        """Cache job search results."""
        try:
            cache_key = self._generate_cache_key(platform, category, keywords)
            cache_file = self._get_cache_file_path(cache_key)
            
            # Prepare cache data
            cache_data = {
                'platform': platform,
                'category': category,
                'keywords': keywords,
                'jobs': jobs,
                'cached_at': datetime.now().isoformat(),
                'job_count': len(jobs)
            }
            
            # Check cache size before writing
            if self._should_evict_cache():
                self._evict_oldest_cache()
            
            # Write to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached {len(jobs)} jobs for {platform}:{category}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching jobs: {str(e)}")
            return False
    
    def _is_cache_expired(self, cache_file: Path) -> bool:
        """Check if cache file is expired."""
        try:
            stat = cache_file.stat()
            file_age = time.time() - stat.st_mtime
            return file_age > self.cache_ttl
        except Exception:
            return True
    
    def _should_evict_cache(self) -> bool:
        """Check if we should evict old cache files."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
            return total_size > self.max_cache_size
        except Exception:
            return False
    
    def _evict_oldest_cache(self):
        """Evict the oldest cache files to free up space."""
        try:
            cache_files = []
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    stat = cache_file.stat()
                    cache_files.append((cache_file, stat.st_mtime))
                except Exception:
                    continue
            
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x[1])
            
            # Remove oldest files until we're under the limit
            for cache_file, _ in cache_files:
                try:
                    cache_file.unlink()
                    self.cache_stats['evictions'] += 1
                    logger.info(f"Evicted cache file: {cache_file.name}")
                    
                    # Check if we're under the limit now
                    total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
                    if total_size <= self.max_cache_size:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error evicting cache file {cache_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error during cache eviction: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'cache_files': len(cache_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'hit_rate': round(self.cache_stats['hits'] / max(1, self.cache_stats['hits'] + self.cache_stats['misses']) * 100, 2),
                'evictions': self.cache_stats['evictions']
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def clear_cache(self) -> bool:
        """Clear all cached data."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            
            logger.info("Cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def warm_cache(self, platforms: List[str], categories: List[str]) -> None:
        """Warm up cache with common searches."""
        logger.info("Warming up cache with common searches...")
        
        # This could be extended to pre-fetch common job searches
        # For now, just log the intention
        for platform in platforms:
            for category in categories:
                logger.info(f"Cache warming: {platform}:{category}")
    
    def get_cache_info(self) -> str:
        """Get human-readable cache information."""
        stats = self.get_cache_stats()
        
        info = f"""
📊 CACHE INFORMATION:
====================
📁 Cache Directory: {self.cache_dir}
📄 Cache Files: {stats.get('cache_files', 0)}
💾 Total Size: {stats.get('total_size_mb', 0)} MB
🎯 Cache Hits: {stats.get('hits', 0)}
❌ Cache Misses: {stats.get('misses', 0)}
📈 Hit Rate: {stats.get('hit_rate', 0)}%
🗑️ Evictions: {stats.get('evictions', 0)}
⏰ TTL: {self.cache_ttl} seconds
"""
        return info
