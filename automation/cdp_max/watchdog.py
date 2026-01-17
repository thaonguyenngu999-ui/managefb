"""
Crash/Freeze Containment MAX - Watchdog system

Features:
- Detect hung state (no events, no progress)
- Hard timeout enforcement
- Cleanup: close tab/context, kill child processes
- Poisoned context handling: mark bad contexts, don't reuse
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
import threading
import time
import os
import signal


class HealthStatus(Enum):
    """Health status for monitored entities"""
    HEALTHY = auto()
    DEGRADED = auto()
    UNRESPONSIVE = auto()
    DEAD = auto()


@dataclass
class WatchdogConfig:
    """Watchdog configuration"""
    # Heartbeat
    heartbeat_interval_ms: int = 5000
    heartbeat_timeout_ms: int = 15000

    # Progress monitoring
    progress_timeout_ms: int = 60000  # Max time without progress
    event_timeout_ms: int = 30000     # Max time without events

    # Hard timeout
    job_hard_timeout_ms: int = 600000  # 10 minutes absolute max

    # Poisoned context
    max_failures_before_poison: int = 3
    poison_cooldown_ms: int = 300000  # 5 minutes before retry poisoned


@dataclass
class ContextHealth:
    """Health tracking for a context (tab/browser)"""
    context_id: str
    status: HealthStatus = HealthStatus.HEALTHY
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    last_event: str = field(default_factory=lambda: datetime.now().isoformat())
    last_progress: str = field(default_factory=lambda: datetime.now().isoformat())
    failure_count: int = 0
    poisoned: bool = False
    poisoned_at: Optional[str] = None
    poisoned_reason: Optional[str] = None


class Watchdog:
    """
    Watchdog for monitoring and containing failures

    Responsibilities:
    - Monitor health of contexts
    - Detect hung/unresponsive states
    - Enforce hard timeouts
    - Mark and track poisoned contexts
    """

    def __init__(self, config: WatchdogConfig = None):
        self.config = config or WatchdogConfig()

        # Context tracking
        self._contexts: Dict[str, ContextHealth] = {}
        self._lock = threading.Lock()

        # Watchdog thread
        self._running = False
        self._watchdog_thread: Optional[threading.Thread] = None

        # Callbacks
        self._on_unhealthy: Optional[Callable[[str, HealthStatus], None]] = None
        self._on_timeout: Optional[Callable[[str], None]] = None
        self._on_poisoned: Optional[Callable[[str], None]] = None

        # Kill handlers
        self._kill_handlers: Dict[str, Callable[[], bool]] = {}

    def start(self):
        """Start the watchdog"""
        self._running = True
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def stop(self):
        """Stop the watchdog"""
        self._running = False
        if self._watchdog_thread:
            self._watchdog_thread.join(timeout=5)

    def set_callbacks(self,
                     on_unhealthy: Callable[[str, HealthStatus], None] = None,
                     on_timeout: Callable[[str], None] = None,
                     on_poisoned: Callable[[str], None] = None):
        """Set watchdog callbacks"""
        self._on_unhealthy = on_unhealthy
        self._on_timeout = on_timeout
        self._on_poisoned = on_poisoned

    def register_context(self, context_id: str, kill_handler: Callable[[], bool] = None):
        """Register a context for monitoring"""
        with self._lock:
            self._contexts[context_id] = ContextHealth(context_id=context_id)
            if kill_handler:
                self._kill_handlers[context_id] = kill_handler

    def unregister_context(self, context_id: str):
        """Unregister a context"""
        with self._lock:
            self._contexts.pop(context_id, None)
            self._kill_handlers.pop(context_id, None)

    def heartbeat(self, context_id: str):
        """Record heartbeat for a context"""
        with self._lock:
            if context_id in self._contexts:
                ctx = self._contexts[context_id]
                ctx.last_heartbeat = datetime.now().isoformat()
                if ctx.status == HealthStatus.UNRESPONSIVE:
                    ctx.status = HealthStatus.DEGRADED

    def record_event(self, context_id: str):
        """Record event activity for a context"""
        with self._lock:
            if context_id in self._contexts:
                ctx = self._contexts[context_id]
                ctx.last_event = datetime.now().isoformat()

    def record_progress(self, context_id: str):
        """Record progress for a context"""
        with self._lock:
            if context_id in self._contexts:
                ctx = self._contexts[context_id]
                ctx.last_progress = datetime.now().isoformat()
                if ctx.status in [HealthStatus.DEGRADED, HealthStatus.UNRESPONSIVE]:
                    ctx.status = HealthStatus.HEALTHY

    def record_failure(self, context_id: str, reason: str = None):
        """Record a failure for a context"""
        with self._lock:
            if context_id in self._contexts:
                ctx = self._contexts[context_id]
                ctx.failure_count += 1

                if ctx.failure_count >= self.config.max_failures_before_poison:
                    self._poison_context(context_id, reason or "Max failures exceeded")

    def _poison_context(self, context_id: str, reason: str):
        """Mark context as poisoned"""
        ctx = self._contexts.get(context_id)
        if ctx and not ctx.poisoned:
            ctx.poisoned = True
            ctx.poisoned_at = datetime.now().isoformat()
            ctx.poisoned_reason = reason
            ctx.status = HealthStatus.DEAD

            if self._on_poisoned:
                try:
                    self._on_poisoned(context_id)
                except:
                    pass

    def is_poisoned(self, context_id: str) -> bool:
        """Check if context is poisoned"""
        with self._lock:
            ctx = self._contexts.get(context_id)
            if not ctx:
                return False

            if not ctx.poisoned:
                return False

            # Check cooldown
            if ctx.poisoned_at:
                poisoned_time = datetime.fromisoformat(ctx.poisoned_at)
                elapsed = (datetime.now() - poisoned_time).total_seconds() * 1000
                if elapsed >= self.config.poison_cooldown_ms:
                    # Cooldown passed, give it another chance
                    ctx.poisoned = False
                    ctx.failure_count = 0
                    ctx.status = HealthStatus.DEGRADED
                    return False

            return True

    def get_health(self, context_id: str) -> Optional[ContextHealth]:
        """Get health status for a context"""
        with self._lock:
            return self._contexts.get(context_id)

    def get_all_health(self) -> Dict[str, ContextHealth]:
        """Get health for all contexts"""
        with self._lock:
            return {k: v for k, v in self._contexts.items()}

    def _watchdog_loop(self):
        """Main watchdog monitoring loop"""
        while self._running:
            now = datetime.now()

            contexts_to_check = []
            with self._lock:
                contexts_to_check = list(self._contexts.items())

            for context_id, ctx in contexts_to_check:
                if ctx.poisoned:
                    continue

                # Check heartbeat timeout
                last_hb = datetime.fromisoformat(ctx.last_heartbeat)
                hb_elapsed = (now - last_hb).total_seconds() * 1000

                if hb_elapsed > self.config.heartbeat_timeout_ms:
                    self._handle_timeout(context_id, ctx, "heartbeat")
                    continue

                # Check event timeout
                last_event = datetime.fromisoformat(ctx.last_event)
                event_elapsed = (now - last_event).total_seconds() * 1000

                if event_elapsed > self.config.event_timeout_ms:
                    if ctx.status == HealthStatus.HEALTHY:
                        ctx.status = HealthStatus.DEGRADED
                        if self._on_unhealthy:
                            try:
                                self._on_unhealthy(context_id, HealthStatus.DEGRADED)
                            except:
                                pass

                # Check progress timeout
                last_progress = datetime.fromisoformat(ctx.last_progress)
                progress_elapsed = (now - last_progress).total_seconds() * 1000

                if progress_elapsed > self.config.progress_timeout_ms:
                    self._handle_timeout(context_id, ctx, "progress")
                    continue

            time.sleep(1)  # Check every second

    def _handle_timeout(self, context_id: str, ctx: ContextHealth, timeout_type: str):
        """Handle a timeout condition"""
        with self._lock:
            ctx.status = HealthStatus.UNRESPONSIVE

        # Notify callback
        if self._on_timeout:
            try:
                self._on_timeout(context_id)
            except:
                pass

        # Try to kill the context
        self.kill_context(context_id)

    def kill_context(self, context_id: str) -> bool:
        """Attempt to kill a context"""
        kill_handler = self._kill_handlers.get(context_id)

        if kill_handler:
            try:
                return kill_handler()
            except:
                pass

        return False

    def enforce_hard_timeout(self, context_id: str, start_time: datetime) -> bool:
        """
        Check and enforce hard timeout

        Returns True if timeout exceeded (job should be killed)
        """
        elapsed = (datetime.now() - start_time).total_seconds() * 1000

        if elapsed > self.config.job_hard_timeout_ms:
            # Hard timeout exceeded
            with self._lock:
                if context_id in self._contexts:
                    self._contexts[context_id].status = HealthStatus.DEAD

            # Kill the context
            self.kill_context(context_id)
            return True

        return False

    def get_status_summary(self) -> Dict:
        """Get summary of all context health"""
        with self._lock:
            total = len(self._contexts)
            healthy = sum(1 for c in self._contexts.values() if c.status == HealthStatus.HEALTHY)
            degraded = sum(1 for c in self._contexts.values() if c.status == HealthStatus.DEGRADED)
            unresponsive = sum(1 for c in self._contexts.values() if c.status == HealthStatus.UNRESPONSIVE)
            dead = sum(1 for c in self._contexts.values() if c.status == HealthStatus.DEAD)
            poisoned = sum(1 for c in self._contexts.values() if c.poisoned)

            return {
                'total': total,
                'healthy': healthy,
                'degraded': degraded,
                'unresponsive': unresponsive,
                'dead': dead,
                'poisoned': poisoned
            }


class ProcessWatchdog:
    """
    Watchdog for child processes (browser, etc.)

    Monitors process health and can kill runaway processes.
    """

    def __init__(self):
        self._processes: Dict[int, Dict] = {}
        self._lock = threading.Lock()

    def register_process(self, pid: int, name: str = "", max_memory_mb: int = 0):
        """Register a process for monitoring"""
        with self._lock:
            self._processes[pid] = {
                'name': name,
                'started_at': datetime.now().isoformat(),
                'max_memory_mb': max_memory_mb
            }

    def unregister_process(self, pid: int):
        """Unregister a process"""
        with self._lock:
            self._processes.pop(pid, None)

    def is_alive(self, pid: int) -> bool:
        """Check if process is alive"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kill a process"""
        try:
            if force:
                os.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGTERM)

            # Wait briefly for process to terminate
            time.sleep(0.5)

            if self.is_alive(pid):
                # Force kill if still alive
                os.kill(pid, signal.SIGKILL)

            with self._lock:
                self._processes.pop(pid, None)

            return True
        except:
            return False

    def get_process_memory(self, pid: int) -> Optional[int]:
        """Get process memory usage in MB"""
        try:
            # Linux-specific
            with open(f'/proc/{pid}/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # Value is in kB
                        kb = int(line.split()[1])
                        return kb // 1024
        except:
            pass
        return None

    def check_memory_limits(self) -> List[int]:
        """Check all processes for memory limit violations"""
        violators = []

        with self._lock:
            processes = list(self._processes.items())

        for pid, info in processes:
            if not self.is_alive(pid):
                continue

            max_mem = info.get('max_memory_mb', 0)
            if max_mem > 0:
                current_mem = self.get_process_memory(pid)
                if current_mem and current_mem > max_mem:
                    violators.append(pid)

        return violators
