"""
Recovery MAX - Multi-tier technical self-recovery

Recovery levels:
1. Step retry (light) - Retry the current step
2. State retry (medium) - Retry from current state
3. Recreate context (heavy) - Create new tab/context
4. Restart browser (heaviest) - Full browser restart

Known-safe reset points: locations where we can safely return without breaking logic.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import time
import threading

from .observability import ReasonCode, FailureReason, get_observability


class RecoveryLevel(Enum):
    """Recovery levels from lightest to heaviest"""
    NONE = 0           # No recovery needed
    STEP_RETRY = 1     # Retry current step
    STATE_RETRY = 2    # Retry from current state
    RECREATE_TAB = 3   # Close and reopen tab
    RECREATE_CONTEXT = 4  # Create new browser context
    RESTART_BROWSER = 5   # Full browser restart


@dataclass
class RecoveryResult:
    """Result from a recovery attempt"""
    success: bool
    level: RecoveryLevel
    attempts: int
    elapsed_ms: int
    error: Optional[str] = None
    reason: Optional[FailureReason] = None
    recovered_to: Optional[str] = None  # State/point recovered to


@dataclass
class SafeResetPoint:
    """A known-safe point where recovery can return to"""
    name: str
    state: str
    verify_fn: Callable[[], bool]  # Function to verify we're at this point
    setup_fn: Optional[Callable[[], bool]] = None  # Function to set up from this point
    data: Dict = field(default_factory=dict)


@dataclass
class RecoveryConfig:
    """Configuration for recovery behavior"""
    # Step retry
    max_step_retries: int = 3
    step_retry_delay_ms: int = 500
    step_retry_backoff: float = 1.5

    # State retry
    max_state_retries: int = 2
    state_retry_delay_ms: int = 2000

    # Context recreation
    max_recreate_attempts: int = 2
    recreate_delay_ms: int = 5000

    # Browser restart
    max_restart_attempts: int = 1
    restart_delay_ms: int = 10000

    # Error classification
    retriable_errors: List[ReasonCode] = field(default_factory=lambda: [
        ReasonCode.TIMEOUT_STEP,
        ReasonCode.TIMEOUT_NETWORK,
        ReasonCode.ELEMENT_NOT_FOUND,
        ReasonCode.ELEMENT_NOT_CLICKABLE,
        ReasonCode.ELEMENT_COVERED,
        ReasonCode.NETWORK_ERROR,
        ReasonCode.CDP_COMMAND_FAILED,
    ])

    context_errors: List[ReasonCode] = field(default_factory=lambda: [
        ReasonCode.TARGET_CRASHED,
        ReasonCode.TARGET_CLOSED,
        ReasonCode.CDP_DISCONNECTED,
        ReasonCode.ELEMENT_DETACHED,
    ])

    browser_errors: List[ReasonCode] = field(default_factory=lambda: [
        ReasonCode.BROWSER_CRASHED,
        ReasonCode.BROWSER_HUNG,
        ReasonCode.BROWSER_NOT_RESPONDING,
        ReasonCode.CDP_RECONNECT_FAILED,
    ])


class RecoveryManager:
    """
    Manages technical self-recovery

    Coordinates recovery attempts at different levels,
    respects safe reset points, and tracks recovery history.
    """

    def __init__(self, config: RecoveryConfig = None):
        self.config = config or RecoveryConfig()
        self._obs = get_observability()

        # Reset points registry
        self._reset_points: Dict[str, SafeResetPoint] = {}
        self._current_reset_point: Optional[str] = None

        # Recovery history
        self._recovery_history: List[Dict] = []
        self._lock = threading.Lock()

        # Callbacks for different recovery levels
        self._on_step_retry: Optional[Callable[[int], None]] = None
        self._on_state_retry: Optional[Callable[[str], None]] = None
        self._on_recreate_context: Optional[Callable[[], bool]] = None
        self._on_restart_browser: Optional[Callable[[], bool]] = None

    def register_reset_point(self, point: SafeResetPoint):
        """Register a known-safe reset point"""
        with self._lock:
            self._reset_points[point.name] = point

    def set_current_reset_point(self, name: str):
        """Set current position to a reset point"""
        with self._lock:
            if name in self._reset_points:
                self._current_reset_point = name

    def set_callbacks(self,
                     on_step_retry: Callable[[int], None] = None,
                     on_state_retry: Callable[[str], None] = None,
                     on_recreate_context: Callable[[], bool] = None,
                     on_restart_browser: Callable[[], bool] = None):
        """Set recovery callbacks"""
        self._on_step_retry = on_step_retry
        self._on_state_retry = on_state_retry
        self._on_recreate_context = on_recreate_context
        self._on_restart_browser = on_restart_browser

    def classify_error(self, reason: FailureReason) -> RecoveryLevel:
        """Classify error and determine recovery level"""
        code = reason.code

        # Non-recoverable errors
        if code in [ReasonCode.VALIDATION_FAILED, ReasonCode.GUARD_REJECTED]:
            return RecoveryLevel.NONE

        # Browser-level errors
        if code in self.config.browser_errors:
            return RecoveryLevel.RESTART_BROWSER

        # Context-level errors
        if code in self.config.context_errors:
            return RecoveryLevel.RECREATE_CONTEXT

        # Retriable errors at step level
        if code in self.config.retriable_errors:
            return RecoveryLevel.STEP_RETRY

        # Default to state retry for unknown errors
        if reason.recoverable:
            return RecoveryLevel.STATE_RETRY

        return RecoveryLevel.NONE

    def attempt_recovery(self, reason: FailureReason, current_state: str,
                        step_fn: Callable[[], Tuple[bool, Any]] = None) -> RecoveryResult:
        """
        Attempt recovery based on error type

        Args:
            reason: The failure reason
            current_state: Current state machine state
            step_fn: Function to retry if step-level recovery

        Returns:
            RecoveryResult with success status and details
        """
        start_time = datetime.now()
        level = self.classify_error(reason)

        if level == RecoveryLevel.NONE:
            return RecoveryResult(
                success=False,
                level=level,
                attempts=0,
                elapsed_ms=0,
                error="Non-recoverable error",
                reason=FailureReason(
                    code=ReasonCode.RECOVERY_EXHAUSTED,
                    message="Error is not recoverable"
                )
            )

        # Try recovery levels from lightest to heaviest
        result = None

        if level == RecoveryLevel.STEP_RETRY and step_fn:
            result = self._attempt_step_retry(step_fn)
            if result.success:
                self._record_recovery(level, True, current_state)
                return result

        if level.value <= RecoveryLevel.STATE_RETRY.value:
            result = self._attempt_state_retry(current_state)
            if result.success:
                self._record_recovery(RecoveryLevel.STATE_RETRY, True, current_state)
                return result

        if level.value <= RecoveryLevel.RECREATE_CONTEXT.value:
            result = self._attempt_recreate_context()
            if result.success:
                self._record_recovery(RecoveryLevel.RECREATE_CONTEXT, True, current_state)
                return result

        if level.value <= RecoveryLevel.RESTART_BROWSER.value:
            result = self._attempt_restart_browser()
            if result.success:
                self._record_recovery(RecoveryLevel.RESTART_BROWSER, True, current_state)
                return result

        # All recovery attempts failed
        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        self._record_recovery(level, False, current_state)

        return RecoveryResult(
            success=False,
            level=level,
            attempts=result.attempts if result else 0,
            elapsed_ms=elapsed,
            error="All recovery attempts exhausted",
            reason=FailureReason(
                code=ReasonCode.RECOVERY_EXHAUSTED,
                message="Could not recover after all attempts"
            )
        )

    def _attempt_step_retry(self, step_fn: Callable[[], Tuple[bool, Any]]) -> RecoveryResult:
        """Attempt step-level retry"""
        start_time = datetime.now()
        delay = self.config.step_retry_delay_ms

        for attempt in range(self.config.max_step_retries):
            if self._on_step_retry:
                try:
                    self._on_step_retry(attempt + 1)
                except:
                    pass

            time.sleep(delay / 1000)

            try:
                success, result = step_fn()
                if success:
                    elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                    return RecoveryResult(
                        success=True,
                        level=RecoveryLevel.STEP_RETRY,
                        attempts=attempt + 1,
                        elapsed_ms=elapsed,
                        recovered_to="step_complete"
                    )
            except Exception as e:
                pass

            delay = int(delay * self.config.step_retry_backoff)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return RecoveryResult(
            success=False,
            level=RecoveryLevel.STEP_RETRY,
            attempts=self.config.max_step_retries,
            elapsed_ms=elapsed,
            error="Step retry exhausted"
        )

    def _attempt_state_retry(self, current_state: str) -> RecoveryResult:
        """Attempt state-level retry"""
        start_time = datetime.now()

        # Find nearest reset point
        reset_point = self._find_nearest_reset_point(current_state)

        for attempt in range(self.config.max_state_retries):
            if self._on_state_retry:
                try:
                    self._on_state_retry(reset_point.name if reset_point else current_state)
                except:
                    pass

            time.sleep(self.config.state_retry_delay_ms / 1000)

            # Try to verify we can recover to reset point
            if reset_point:
                try:
                    if reset_point.verify_fn():
                        # We're at the reset point
                        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                        return RecoveryResult(
                            success=True,
                            level=RecoveryLevel.STATE_RETRY,
                            attempts=attempt + 1,
                            elapsed_ms=elapsed,
                            recovered_to=reset_point.name
                        )

                    # Try to set up to reset point
                    if reset_point.setup_fn:
                        if reset_point.setup_fn():
                            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                            return RecoveryResult(
                                success=True,
                                level=RecoveryLevel.STATE_RETRY,
                                attempts=attempt + 1,
                                elapsed_ms=elapsed,
                                recovered_to=reset_point.name
                            )
                except:
                    pass

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return RecoveryResult(
            success=False,
            level=RecoveryLevel.STATE_RETRY,
            attempts=self.config.max_state_retries,
            elapsed_ms=elapsed,
            error="State retry exhausted"
        )

    def _attempt_recreate_context(self) -> RecoveryResult:
        """Attempt to recreate tab/context"""
        start_time = datetime.now()

        if not self._on_recreate_context:
            return RecoveryResult(
                success=False,
                level=RecoveryLevel.RECREATE_CONTEXT,
                attempts=0,
                elapsed_ms=0,
                error="No recreate callback registered"
            )

        for attempt in range(self.config.max_recreate_attempts):
            time.sleep(self.config.recreate_delay_ms / 1000)

            try:
                if self._on_recreate_context():
                    elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                    return RecoveryResult(
                        success=True,
                        level=RecoveryLevel.RECREATE_CONTEXT,
                        attempts=attempt + 1,
                        elapsed_ms=elapsed,
                        recovered_to="new_context"
                    )
            except:
                pass

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return RecoveryResult(
            success=False,
            level=RecoveryLevel.RECREATE_CONTEXT,
            attempts=self.config.max_recreate_attempts,
            elapsed_ms=elapsed,
            error="Context recreation exhausted"
        )

    def _attempt_restart_browser(self) -> RecoveryResult:
        """Attempt to restart browser"""
        start_time = datetime.now()

        if not self._on_restart_browser:
            return RecoveryResult(
                success=False,
                level=RecoveryLevel.RESTART_BROWSER,
                attempts=0,
                elapsed_ms=0,
                error="No restart callback registered"
            )

        for attempt in range(self.config.max_restart_attempts):
            time.sleep(self.config.restart_delay_ms / 1000)

            try:
                if self._on_restart_browser():
                    elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                    return RecoveryResult(
                        success=True,
                        level=RecoveryLevel.RESTART_BROWSER,
                        attempts=attempt + 1,
                        elapsed_ms=elapsed,
                        recovered_to="browser_restarted"
                    )
            except:
                pass

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return RecoveryResult(
            success=False,
            level=RecoveryLevel.RESTART_BROWSER,
            attempts=self.config.max_restart_attempts,
            elapsed_ms=elapsed,
            error="Browser restart exhausted"
        )

    def _find_nearest_reset_point(self, current_state: str) -> Optional[SafeResetPoint]:
        """Find the nearest safe reset point"""
        with self._lock:
            if self._current_reset_point and self._current_reset_point in self._reset_points:
                return self._reset_points[self._current_reset_point]

            # Return first reset point that can be verified
            for point in self._reset_points.values():
                try:
                    if point.verify_fn():
                        return point
                except:
                    pass

        return None

    def _record_recovery(self, level: RecoveryLevel, success: bool, state: str):
        """Record recovery attempt in history"""
        with self._lock:
            self._recovery_history.append({
                'level': level.name,
                'success': success,
                'state': state,
                'timestamp': datetime.now().isoformat()
            })

            # Keep only recent history
            if len(self._recovery_history) > 100:
                self._recovery_history = self._recovery_history[-100:]

    def get_recovery_history(self) -> List[Dict]:
        """Get recovery attempt history"""
        with self._lock:
            return self._recovery_history.copy()

    def get_recovery_stats(self) -> Dict:
        """Get recovery statistics"""
        with self._lock:
            total = len(self._recovery_history)
            successful = sum(1 for r in self._recovery_history if r['success'])

            by_level = {}
            for r in self._recovery_history:
                level = r['level']
                if level not in by_level:
                    by_level[level] = {'total': 0, 'success': 0}
                by_level[level]['total'] += 1
                if r['success']:
                    by_level[level]['success'] += 1

            return {
                'total_attempts': total,
                'successful': successful,
                'success_rate': successful / total if total > 0 else 0,
                'by_level': by_level
            }
