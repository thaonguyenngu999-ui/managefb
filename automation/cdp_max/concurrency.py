"""
Concurrency Model MAX - Multi-job orchestration

Features:
- Each job has its own context (logical isolation)
- Serialized per-target: one tab doesn't receive 2 command sequences simultaneously
- Worker pool with quota to avoid overwhelming CDP/browser
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
import threading
import queue
import time

from .observability import ReasonCode, FailureReason, get_observability


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class JobSpec:
    """Specification for a job"""
    job_id: str
    target_id: str  # Tab/target this job operates on
    execute_fn: Callable[[], Any]
    priority: JobPriority = JobPriority.NORMAL
    timeout_ms: int = 300000
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class JobResult:
    """Result from job execution"""
    job_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    reason: Optional[FailureReason] = None
    elapsed_ms: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class JobQueue:
    """
    Priority queue for jobs with target-aware scheduling

    Ensures only one job per target runs at a time.
    """

    def __init__(self):
        self._queue: List[JobSpec] = []
        self._lock = threading.Lock()
        self._active_targets: Set[str] = set()
        self._waiting: Dict[str, threading.Event] = {}

    def enqueue(self, job: JobSpec) -> bool:
        """Add job to queue"""
        with self._lock:
            # Insert by priority (higher priority first)
            inserted = False
            for i, existing in enumerate(self._queue):
                if job.priority.value > existing.priority.value:
                    self._queue.insert(i, job)
                    inserted = True
                    break
            if not inserted:
                self._queue.append(job)
            return True

    def dequeue(self, timeout_ms: int = None) -> Optional[JobSpec]:
        """
        Get next job that can run

        Returns job only if its target is not busy.
        """
        deadline = None
        if timeout_ms:
            deadline = datetime.now().timestamp() + (timeout_ms / 1000)

        while True:
            with self._lock:
                for i, job in enumerate(self._queue):
                    if job.target_id not in self._active_targets:
                        # Can run this job
                        self._queue.pop(i)
                        self._active_targets.add(job.target_id)
                        return job

            # No eligible job, wait or return
            if deadline is None or datetime.now().timestamp() >= deadline:
                return None

            time.sleep(0.05)

    def release_target(self, target_id: str):
        """Mark target as available"""
        with self._lock:
            self._active_targets.discard(target_id)

    def get_queue_length(self) -> int:
        """Get number of pending jobs"""
        with self._lock:
            return len(self._queue)

    def get_active_targets(self) -> Set[str]:
        """Get set of busy targets"""
        with self._lock:
            return self._active_targets.copy()

    def clear(self):
        """Clear all pending jobs"""
        with self._lock:
            self._queue.clear()


class CommandThrottle:
    """
    Throttles CDP commands to prevent overwhelming the browser

    Features:
    - Rate limiting (max commands per second)
    - Concurrent command limiting
    - Backoff on high latency
    """

    def __init__(self, max_commands_per_second: int = 50,
                 max_concurrent: int = 20):
        self.max_commands_per_second = max_commands_per_second
        self.max_concurrent = max_concurrent

        self._command_times: List[float] = []
        self._concurrent_semaphore = threading.Semaphore(max_concurrent)
        self._lock = threading.Lock()

        # Adaptive throttling
        self._recent_latencies: List[float] = []
        self._throttle_factor = 1.0

    def acquire(self, timeout_ms: int = 30000) -> bool:
        """
        Acquire permission to send a command

        Returns True if command can be sent, False if throttled.
        """
        # Check rate limit
        with self._lock:
            now = time.time()
            # Remove old timestamps
            self._command_times = [t for t in self._command_times if now - t < 1.0]

            if len(self._command_times) >= self.max_commands_per_second * self._throttle_factor:
                # Rate limited - wait
                sleep_time = 1.0 / self.max_commands_per_second
                time.sleep(sleep_time)

        # Check concurrent limit
        acquired = self._concurrent_semaphore.acquire(timeout=timeout_ms / 1000)
        if not acquired:
            return False

        # Record this command
        with self._lock:
            self._command_times.append(time.time())

        return True

    def release(self, latency_ms: float = 0):
        """Release command slot and record latency"""
        self._concurrent_semaphore.release()

        if latency_ms > 0:
            with self._lock:
                self._recent_latencies.append(latency_ms)
                if len(self._recent_latencies) > 100:
                    self._recent_latencies = self._recent_latencies[-100:]

                # Adaptive throttling based on latency
                avg_latency = sum(self._recent_latencies) / len(self._recent_latencies)
                if avg_latency > 500:  # High latency
                    self._throttle_factor = max(0.5, self._throttle_factor - 0.1)
                elif avg_latency < 100:  # Low latency
                    self._throttle_factor = min(1.0, self._throttle_factor + 0.05)

    def get_stats(self) -> Dict:
        """Get throttle statistics"""
        with self._lock:
            avg_latency = 0
            if self._recent_latencies:
                avg_latency = sum(self._recent_latencies) / len(self._recent_latencies)

            return {
                'throttle_factor': self._throttle_factor,
                'avg_latency_ms': avg_latency,
                'commands_last_second': len(self._command_times),
                'concurrent_available': self._concurrent_semaphore._value
            }


class WorkerPool:
    """
    Worker pool for parallel job execution

    Features:
    - Configurable pool size
    - Job result callbacks
    - Graceful shutdown
    """

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Dict[str, Future] = {}
        self._results: Dict[str, JobResult] = {}
        self._lock = threading.Lock()
        self._shutdown = False
        self._obs = get_observability()

    def start(self):
        """Start the worker pool"""
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._shutdown = False

    def stop(self, wait: bool = True):
        """Stop the worker pool"""
        self._shutdown = True
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None

    def submit(self, job: JobSpec, callback: Callable[[JobResult], None] = None) -> bool:
        """Submit a job for execution"""
        if self._shutdown or not self._executor:
            return False

        def execute_job():
            start_time = datetime.now()
            started_at = start_time.isoformat()

            try:
                result = job.execute_fn()
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

                job_result = JobResult(
                    job_id=job.job_id,
                    success=True,
                    result=result,
                    elapsed_ms=elapsed,
                    started_at=started_at,
                    completed_at=datetime.now().isoformat()
                )

            except Exception as e:
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                job_result = JobResult(
                    job_id=job.job_id,
                    success=False,
                    error=str(e),
                    reason=FailureReason.from_exception(e),
                    elapsed_ms=elapsed,
                    started_at=started_at,
                    completed_at=datetime.now().isoformat()
                )

            with self._lock:
                self._results[job.job_id] = job_result

            if callback:
                try:
                    callback(job_result)
                except:
                    pass

            return job_result

        future = self._executor.submit(execute_job)

        with self._lock:
            self._futures[job.job_id] = future

        return True

    def get_result(self, job_id: str, timeout_ms: int = None) -> Optional[JobResult]:
        """Get result for a job (blocking)"""
        with self._lock:
            future = self._futures.get(job_id)
            existing_result = self._results.get(job_id)

        if existing_result:
            return existing_result

        if not future:
            return None

        try:
            timeout = timeout_ms / 1000 if timeout_ms else None
            future.result(timeout=timeout)
        except:
            pass

        with self._lock:
            return self._results.get(job_id)

    def get_active_count(self) -> int:
        """Get number of active jobs"""
        with self._lock:
            return sum(1 for f in self._futures.values() if not f.done())

    def get_completed_count(self) -> int:
        """Get number of completed jobs"""
        with self._lock:
            return len(self._results)


class ConcurrencyManager:
    """
    Central concurrency manager for CDP automation

    Coordinates:
    - Job queue with priority
    - Worker pool
    - Per-target serialization
    - Command throttling
    """

    def __init__(self, max_workers: int = 5, max_commands_per_second: int = 50):
        self.job_queue = JobQueue()
        self.worker_pool = WorkerPool(max_workers)
        self.throttle = CommandThrottle(max_commands_per_second)

        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the concurrency manager"""
        self._running = True
        self.worker_pool.start()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self, wait: bool = True):
        """Stop the concurrency manager"""
        self._running = False
        self.worker_pool.stop(wait)

    def _scheduler_loop(self):
        """Main scheduler loop - picks jobs from queue and submits to pool"""
        while self._running:
            # Get next eligible job
            job = self.job_queue.dequeue(timeout_ms=100)

            if job:
                # Submit to worker pool
                def on_complete(result: JobResult):
                    self.job_queue.release_target(job.target_id)

                self.worker_pool.submit(job, callback=on_complete)

            time.sleep(0.01)

    def submit_job(self, job_id: str, target_id: str, execute_fn: Callable,
                   priority: JobPriority = JobPriority.NORMAL,
                   timeout_ms: int = 300000) -> bool:
        """Submit a job for execution"""
        job = JobSpec(
            job_id=job_id,
            target_id=target_id,
            execute_fn=execute_fn,
            priority=priority,
            timeout_ms=timeout_ms
        )
        return self.job_queue.enqueue(job)

    def wait_for_job(self, job_id: str, timeout_ms: int = None) -> Optional[JobResult]:
        """Wait for a job to complete"""
        return self.worker_pool.get_result(job_id, timeout_ms)

    def get_status(self) -> Dict:
        """Get concurrency manager status"""
        return {
            'running': self._running,
            'queue_length': self.job_queue.get_queue_length(),
            'active_targets': list(self.job_queue.get_active_targets()),
            'active_workers': self.worker_pool.get_active_count(),
            'completed_jobs': self.worker_pool.get_completed_count(),
            'throttle_stats': self.throttle.get_stats()
        }
