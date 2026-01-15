"""
Performance & Determinism MAX - Optimization without sacrificing reliability

Features:
- Command batching: reduce CDP chatter
- Locator caching with staleness detection
- Screenshot/trace limiting by policy
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import threading
import time
import hashlib


@dataclass
class CachedLocator:
    """Cached locator result"""
    selector: str
    node_id: int
    object_id: str
    cached_at: str
    last_verified: str
    hit_count: int = 0
    stale: bool = False

    def is_expired(self, max_age_ms: int) -> bool:
        """Check if cache entry is expired"""
        cached_time = datetime.fromisoformat(self.cached_at)
        age = (datetime.now() - cached_time).total_seconds() * 1000
        return age > max_age_ms


class LocatorCache:
    """
    Cache for element locators

    Features:
    - Short-lived cache to avoid stale references
    - Automatic staleness detection
    - Cache invalidation on navigation
    """

    def __init__(self, max_age_ms: int = 5000, max_size: int = 100):
        self.max_age_ms = max_age_ms
        self.max_size = max_size
        self._cache: Dict[str, CachedLocator] = {}
        self._lock = threading.Lock()
        self._enabled = True

    def enable(self):
        """Enable caching"""
        self._enabled = True

    def disable(self):
        """Disable caching"""
        self._enabled = False
        self.clear()

    def get(self, selector: str) -> Optional[CachedLocator]:
        """Get cached locator if valid"""
        if not self._enabled:
            return None

        with self._lock:
            cached = self._cache.get(selector)
            if not cached:
                return None

            if cached.stale or cached.is_expired(self.max_age_ms):
                del self._cache[selector]
                return None

            cached.hit_count += 1
            return cached

    def set(self, selector: str, node_id: int, object_id: str):
        """Cache a locator"""
        if not self._enabled:
            return

        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[selector] = CachedLocator(
                selector=selector,
                node_id=node_id,
                object_id=object_id,
                cached_at=datetime.now().isoformat(),
                last_verified=datetime.now().isoformat()
            )

    def invalidate(self, selector: str = None):
        """Invalidate cache entry or all entries"""
        with self._lock:
            if selector:
                self._cache.pop(selector, None)
            else:
                self._cache.clear()

    def mark_stale(self, selector: str):
        """Mark a cached entry as stale"""
        with self._lock:
            if selector in self._cache:
                self._cache[selector].stale = True

    def clear(self):
        """Clear all cache"""
        with self._lock:
            self._cache.clear()

    def _evict_oldest(self):
        """Evict oldest cache entry"""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].cached_at
        )
        del self._cache[oldest_key]

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total_hits = sum(c.hit_count for c in self._cache.values())
            return {
                'enabled': self._enabled,
                'size': len(self._cache),
                'max_size': self.max_size,
                'total_hits': total_hits,
                'entries': [
                    {
                        'selector': c.selector[:50],
                        'hits': c.hit_count,
                        'stale': c.stale
                    }
                    for c in self._cache.values()
                ]
            }


@dataclass
class BatchedCommand:
    """A command to be batched"""
    method: str
    params: Dict
    callback: Optional[Callable[[Dict], None]] = None


class CommandBatcher:
    """
    Batches multiple CDP commands for efficiency

    Features:
    - Batch evaluate multiple JS expressions
    - Reduce round-trips
    - Smart grouping of related commands
    """

    def __init__(self, session, max_batch_size: int = 10,
                 batch_delay_ms: int = 50):
        self._session = session
        self.max_batch_size = max_batch_size
        self.batch_delay_ms = batch_delay_ms

        self._pending: List[BatchedCommand] = []
        self._lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None

    def add(self, method: str, params: Dict = None,
            callback: Callable[[Dict], None] = None):
        """Add command to batch"""
        cmd = BatchedCommand(method=method, params=params or {}, callback=callback)

        with self._lock:
            self._pending.append(cmd)

            if len(self._pending) >= self.max_batch_size:
                self._flush()
            elif not self._flush_timer:
                self._flush_timer = threading.Timer(
                    self.batch_delay_ms / 1000,
                    self._flush
                )
                self._flush_timer.start()

    def _flush(self):
        """Flush pending commands"""
        with self._lock:
            if self._flush_timer:
                self._flush_timer.cancel()
                self._flush_timer = None

            commands = self._pending.copy()
            self._pending.clear()

        if not commands:
            return

        # Group by method for potential optimization
        js_evaluates = [c for c in commands if c.method == 'Runtime.evaluate']
        other_commands = [c for c in commands if c.method != 'Runtime.evaluate']

        # Batch JS evaluates into single call
        if js_evaluates:
            self._batch_js_evaluates(js_evaluates)

        # Execute other commands individually (could be parallelized)
        for cmd in other_commands:
            try:
                result = self._session.send_command(cmd.method, cmd.params)
                if cmd.callback:
                    cmd.callback(result.result if result.success else {'error': result.error})
            except Exception as e:
                if cmd.callback:
                    cmd.callback({'error': str(e)})

    def _batch_js_evaluates(self, commands: List[BatchedCommand]):
        """Batch multiple JS evaluations into one"""
        if not commands:
            return

        if len(commands) == 1:
            # Single command, no batching needed
            cmd = commands[0]
            try:
                result = self._session.send_command(cmd.method, cmd.params)
                if cmd.callback:
                    cmd.callback(result.result if result.success else {'error': result.error})
            except Exception as e:
                if cmd.callback:
                    cmd.callback({'error': str(e)})
            return

        # Build combined expression
        expressions = []
        for i, cmd in enumerate(commands):
            expr = cmd.params.get('expression', '')
            # Wrap each expression to capture result
            expressions.append(f"(() => {{ try {{ return {expr}; }} catch(e) {{ return {{error: e.message}}; }} }})()")

        combined = f"[{', '.join(expressions)}]"

        try:
            result = self._session.send_command('Runtime.evaluate', {
                'expression': combined,
                'returnByValue': True
            })

            if result.success and result.result:
                results = result.result.get('result', {}).get('value', [])
                for i, cmd in enumerate(commands):
                    if cmd.callback and i < len(results):
                        cmd.callback({'result': {'value': results[i]}})
        except Exception as e:
            # Fall back to individual execution
            for cmd in commands:
                try:
                    result = self._session.send_command(cmd.method, cmd.params)
                    if cmd.callback:
                        cmd.callback(result.result if result.success else {'error': result.error})
                except:
                    pass

    def flush_sync(self):
        """Synchronously flush all pending commands"""
        self._flush()


@dataclass
class ScreenshotPolicy:
    """Policy for screenshot capture"""
    enabled: bool = True
    on_error: bool = True
    on_state_change: bool = False
    max_per_job: int = 10
    quality: int = 80  # JPEG quality
    max_width: int = 1920
    max_height: int = 1080


class PerformanceOptimizer:
    """
    Central performance optimizer

    Coordinates caching, batching, and resource limiting.
    """

    def __init__(self, session):
        self._session = session
        self.locator_cache = LocatorCache()
        self.command_batcher = CommandBatcher(session)
        self.screenshot_policy = ScreenshotPolicy()

        # Metrics
        self._metrics = {
            'commands_sent': 0,
            'commands_batched': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'screenshots_taken': 0,
            'screenshots_skipped': 0
        }
        self._lock = threading.Lock()

        # Screenshot counter per job
        self._job_screenshots: Dict[str, int] = {}

    def on_navigation(self):
        """Called when navigation occurs - invalidate caches"""
        self.locator_cache.clear()

    def should_take_screenshot(self, job_id: str, reason: str = 'manual') -> bool:
        """Check if screenshot should be taken per policy"""
        if not self.screenshot_policy.enabled:
            with self._lock:
                self._metrics['screenshots_skipped'] += 1
            return False

        if reason == 'error' and not self.screenshot_policy.on_error:
            with self._lock:
                self._metrics['screenshots_skipped'] += 1
            return False

        if reason == 'state_change' and not self.screenshot_policy.on_state_change:
            with self._lock:
                self._metrics['screenshots_skipped'] += 1
            return False

        # Check per-job limit
        with self._lock:
            count = self._job_screenshots.get(job_id, 0)
            if count >= self.screenshot_policy.max_per_job:
                self._metrics['screenshots_skipped'] += 1
                return False

            self._job_screenshots[job_id] = count + 1
            self._metrics['screenshots_taken'] += 1

        return True

    def reset_job_screenshots(self, job_id: str):
        """Reset screenshot counter for a job"""
        with self._lock:
            self._job_screenshots.pop(job_id, None)

    def record_command(self, batched: bool = False):
        """Record command execution"""
        with self._lock:
            self._metrics['commands_sent'] += 1
            if batched:
                self._metrics['commands_batched'] += 1

    def record_cache_access(self, hit: bool):
        """Record cache access"""
        with self._lock:
            if hit:
                self._metrics['cache_hits'] += 1
            else:
                self._metrics['cache_misses'] += 1

    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        with self._lock:
            metrics = self._metrics.copy()

        metrics['cache_stats'] = self.locator_cache.get_stats()

        # Calculate rates
        total_cache = metrics['cache_hits'] + metrics['cache_misses']
        if total_cache > 0:
            metrics['cache_hit_rate'] = metrics['cache_hits'] / total_cache
        else:
            metrics['cache_hit_rate'] = 0

        return metrics

    def optimize_selector(self, selector: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Get optimized selector result from cache or evaluate

        Returns (node_id, object_id) or (None, None) if not cached
        """
        cached = self.locator_cache.get(selector)
        if cached:
            self.record_cache_access(hit=True)
            return cached.node_id, cached.object_id

        self.record_cache_access(hit=False)
        return None, None

    def cache_selector(self, selector: str, node_id: int, object_id: str):
        """Cache a selector result"""
        self.locator_cache.set(selector, node_id, object_id)
