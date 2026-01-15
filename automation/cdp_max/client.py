"""
CDP Client MAX - Main client bringing all MAX features together

This is the primary interface for CDP automation with all 12 MAX features:
1. Connection layer MAX
2. Deterministic waiting MAX
3. Action layer MAX
4. Selector strategy MAX
5. Event-driven MAX
6. Navigation correctness MAX
7. File I/O MAX
8. Concurrency model MAX
9. Recovery MAX
10. Crash/Freeze containment MAX
11. Performance MAX
12. Observability MAX
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import threading

from .session import CDPSession, SessionConfig, SessionState
from .events import EventEmitter, CDPEvent, EventType
from .targets import TargetManager, Target, TargetType
from .waits import WaitEngine, WaitCondition, WaitResult, ConditionType, DOMCondition
from .selectors import SelectorEngine, Locator, LocatorType, ElementHandle
from .actions import ActionExecutor, ActionResult, Postcondition, IdempotentGuard
from .navigation import NavigationManager, NavigationType, NavigationResult
from .file_io import FileIOManager, UploadResult, DownloadResult
from .recovery import RecoveryManager, RecoveryLevel, RecoveryResult, SafeResetPoint
from .watchdog import Watchdog, WatchdogConfig, HealthStatus
from .performance import PerformanceOptimizer, LocatorCache
from .observability import (
    ObservabilityEngine, ReasonCode, FailureReason,
    StepTrace, JobTrace, get_observability
)


@dataclass
class CDPClientConfig:
    """Configuration for CDP Client MAX"""
    # Session
    remote_port: int = 0
    connect_timeout_ms: int = 30000
    auto_reconnect: bool = True

    # Timeouts (step < state < job)
    step_timeout_ms: int = 10000
    state_timeout_ms: int = 30000
    job_timeout_ms: int = 300000

    # Waits
    stability_window_ms: int = 500
    poll_interval_ms: int = 100

    # Recovery
    enable_recovery: bool = True
    max_step_retries: int = 3
    max_state_retries: int = 2

    # Watchdog
    enable_watchdog: bool = True
    heartbeat_interval_ms: int = 5000

    # Performance
    enable_caching: bool = True
    enable_batching: bool = True
    max_screenshots_per_job: int = 10


class CDPClientMAX:
    """
    Production-grade CDP Client with MAX features

    Usage:
        client = CDPClientMAX(CDPClientConfig(remote_port=9222))
        success, reason = client.connect()

        # Navigate
        result = client.navigate("https://example.com")

        # Find and click
        button = client.by_role("button", "Submit")
        result = client.click(button)

        # Type text
        input_field = client.by_placeholder("Email")
        result = client.type_text(input_field, "test@example.com")

        client.close()
    """

    def __init__(self, config: CDPClientConfig = None):
        self.config = config or CDPClientConfig()

        # Initialize session config
        session_config = SessionConfig(
            remote_port=self.config.remote_port,
            connect_timeout_ms=self.config.connect_timeout_ms,
            auto_reconnect=self.config.auto_reconnect,
            heartbeat_interval_ms=self.config.heartbeat_interval_ms
        )

        # Core components
        self.session = CDPSession(session_config)
        self.events = self.session.events
        self.targets = TargetManager(self.session)
        self.waits = WaitEngine(self.session)
        self.selectors = SelectorEngine(self.session)
        self.actions = ActionExecutor(self.session, self.selectors, self.waits)
        self.navigation = NavigationManager(self.session, self.waits)
        self.file_io = FileIOManager(self.session, self.waits)
        self.recovery = RecoveryManager()
        self.watchdog = Watchdog() if self.config.enable_watchdog else None
        self.performance = PerformanceOptimizer(self.session)
        self.observability = get_observability()

        # Configure waits
        self.waits.step_timeout_ms = self.config.step_timeout_ms
        self.waits.state_timeout_ms = self.config.state_timeout_ms
        self.waits.job_timeout_ms = self.config.job_timeout_ms
        self.waits.stability_window_ms = self.config.stability_window_ms

        # Configure performance
        if not self.config.enable_caching:
            self.performance.locator_cache.disable()
        self.performance.screenshot_policy.max_per_job = self.config.max_screenshots_per_job

        # Job tracking
        self._current_job_id: Optional[str] = None
        self._job_start_time: Optional[datetime] = None

    # ==================== CONNECTION ====================

    def connect(self) -> Tuple[bool, Optional[FailureReason]]:
        """Connect to browser via CDP"""
        success, reason = self.session.connect()

        if success:
            # Initialize targets
            self.targets.initialize()

            # Start watchdog if enabled
            if self.watchdog:
                self.watchdog.start()
                context_id = f"main_{self.config.remote_port}"
                self.watchdog.register_context(context_id)

        return success, reason

    def close(self):
        """Close CDP connection"""
        if self.watchdog:
            self.watchdog.stop()

        self.session.close()

    @property
    def is_connected(self) -> bool:
        return self.session.is_connected

    @property
    def is_ready(self) -> bool:
        return self.session.is_ready

    # ==================== LOCATOR BUILDERS ====================

    def by_role(self, role: str, name: str = None) -> Locator:
        """Create locator by ARIA role"""
        return self.selectors.by_role(role, name)

    def by_aria_label(self, label: str) -> Locator:
        """Create locator by aria-label"""
        return self.selectors.by_aria_label(label)

    def by_test_id(self, test_id: str) -> Locator:
        """Create locator by test ID"""
        return self.selectors.by_test_id(test_id)

    def by_text(self, text: str, exact: bool = False) -> Locator:
        """Create locator by text content"""
        return self.selectors.by_text(text, exact)

    def by_placeholder(self, placeholder: str) -> Locator:
        """Create locator by placeholder"""
        return self.selectors.by_placeholder(placeholder)

    def by_css(self, selector: str) -> Locator:
        """Create locator by CSS selector"""
        return self.selectors.by_css(selector)

    def by_xpath(self, xpath: str) -> Locator:
        """Create locator by XPath"""
        return self.selectors.by_xpath(xpath)

    # ==================== WAITING ====================

    def wait_for(self, condition: WaitCondition, timeout_ms: int = None) -> WaitResult:
        """Wait for a condition"""
        return self.waits.wait_for(condition, timeout_ms)

    def wait_for_element(self, locator: Locator, timeout_ms: int = None) -> WaitResult:
        """Wait for element to exist"""
        return self.waits.wait_for(
            WaitCondition(
                type=ConditionType.ELEMENT_EXISTS,
                selector=locator.to_selector()
            ),
            timeout_ms or self.config.step_timeout_ms
        )

    def wait_for_visible(self, locator: Locator, timeout_ms: int = None) -> WaitResult:
        """Wait for element to be visible"""
        return self.waits.wait_for(
            WaitCondition(
                type=ConditionType.ELEMENT_VISIBLE,
                selector=locator.to_selector()
            ),
            timeout_ms or self.config.step_timeout_ms
        )

    def wait_for_clickable(self, locator: Locator, timeout_ms: int = None) -> WaitResult:
        """Wait for element to be clickable"""
        return self.waits.wait_for(
            WaitCondition(
                type=ConditionType.ELEMENT_CLICKABLE,
                selector=locator.to_selector()
            ),
            timeout_ms or self.config.step_timeout_ms
        )

    def wait_for_network_idle(self, timeout_ms: int = None) -> WaitResult:
        """Wait for network to be idle"""
        return self.waits.wait_for_network_idle(timeout_ms)

    def wait_for_navigation(self, timeout_ms: int = None) -> WaitResult:
        """Wait for navigation to complete"""
        return self.waits.wait_for_navigation(timeout_ms)

    # ==================== ACTIONS ====================

    def click(self, locator: Locator,
              postcondition: Postcondition = None,
              idempotent_guard: IdempotentGuard = None) -> ActionResult:
        """Click element with verification"""
        result = self.actions.click(locator, postcondition, idempotent_guard)

        # Record for watchdog
        if self.watchdog:
            context_id = f"main_{self.config.remote_port}"
            if result.success:
                self.watchdog.record_progress(context_id)
            else:
                self.watchdog.record_failure(context_id, result.error)

        return result

    def type_text(self, locator: Locator, text: str, clear: bool = True,
                  postcondition: Postcondition = None) -> ActionResult:
        """Type text into input with verification"""
        result = self.actions.type_text(locator, text, clear, postcondition)

        if self.watchdog:
            context_id = f"main_{self.config.remote_port}"
            if result.success:
                self.watchdog.record_progress(context_id)

        return result

    def scroll_to(self, locator: Locator) -> ActionResult:
        """Scroll element into view"""
        return self.actions.scroll_to(locator)

    def hover(self, locator: Locator) -> ActionResult:
        """Hover over element"""
        return self.actions.hover(locator)

    # ==================== NAVIGATION ====================

    def navigate(self, url: str, timeout_ms: int = None,
                 wait_until: str = 'load') -> NavigationResult:
        """Navigate to URL"""
        result = self.navigation.navigate(url, timeout_ms or self.config.state_timeout_ms, wait_until)

        # Invalidate caches on navigation
        self.performance.on_navigation()

        if self.watchdog:
            context_id = f"main_{self.config.remote_port}"
            if result.success:
                self.watchdog.record_progress(context_id)

        return result

    def navigate_spa(self, action: Callable, url_pattern: str = None,
                     timeout_ms: int = None) -> NavigationResult:
        """Navigate within SPA"""
        return self.navigation.navigate_spa(action, url_pattern, timeout_ms)

    def go_back(self, timeout_ms: int = None) -> NavigationResult:
        """Navigate back"""
        return self.navigation.go_back(timeout_ms)

    def reload(self, timeout_ms: int = None) -> NavigationResult:
        """Reload page"""
        return self.navigation.reload(timeout_ms)

    def get_current_url(self) -> Optional[str]:
        """Get current URL"""
        return self.session.get_current_url()

    # ==================== FILE I/O ====================

    def upload_file(self, locator: Locator, file_path: str,
                    verify_preview: bool = True) -> UploadResult:
        """Upload file to input"""
        return self.file_io.upload_file(locator.to_selector(), file_path, verify_preview)

    def wait_for_download(self, trigger_action: Callable = None,
                          expected_filename: str = None,
                          timeout_ms: int = 60000) -> DownloadResult:
        """Wait for download to complete"""
        return self.file_io.wait_for_download(trigger_action, expected_filename, timeout_ms)

    # ==================== ELEMENT QUERIES ====================

    def find(self, locator: Locator) -> Optional[ElementHandle]:
        """Find single element"""
        return self.selectors.find(locator)

    def find_all(self, locator: Locator) -> List[ElementHandle]:
        """Find all matching elements"""
        return self.selectors.find_all(locator)

    def exists(self, locator: Locator) -> bool:
        """Check if element exists"""
        result = self.waits.wait_for(
            WaitCondition(type=ConditionType.ELEMENT_EXISTS, selector=locator.to_selector()),
            timeout_ms=1000,
            stability_ms=0
        )
        return result.success

    def is_visible(self, locator: Locator) -> bool:
        """Check if element is visible"""
        result = self.waits.wait_for(
            WaitCondition(type=ConditionType.ELEMENT_VISIBLE, selector=locator.to_selector()),
            timeout_ms=1000,
            stability_ms=0
        )
        return result.success

    # ==================== JS EXECUTION ====================

    def evaluate(self, expression: str) -> Any:
        """Evaluate JavaScript and return result"""
        result = self.session.evaluate_js(expression)
        if result.success and result.result:
            return result.result.get('result', {}).get('value')
        return None

    def execute(self, script: str) -> bool:
        """Execute JavaScript"""
        result = self.session.evaluate_js(script)
        return result.success

    # ==================== SCREENSHOTS ====================

    def take_screenshot(self, job_id: str = None, reason: str = 'manual') -> Optional[str]:
        """Take screenshot if allowed by policy"""
        jid = job_id or self._current_job_id or 'default'

        if not self.performance.should_take_screenshot(jid, reason):
            return None

        result = self.session.send_command('Page.captureScreenshot', {
            'format': 'png',
            'quality': self.performance.screenshot_policy.quality
        })

        if result.success and result.result:
            return result.result.get('data')

        return None

    # ==================== RECOVERY ====================

    def with_recovery(self, action: Callable[[], Any],
                      current_state: str = "unknown") -> Tuple[bool, Any, Optional[FailureReason]]:
        """
        Execute action with automatic recovery

        Returns (success, result, failure_reason)
        """
        if not self.config.enable_recovery:
            try:
                result = action()
                return True, result, None
            except Exception as e:
                return False, None, FailureReason.from_exception(e)

        try:
            result = action()
            return True, result, None
        except Exception as e:
            reason = FailureReason.from_exception(e)

            # Attempt recovery
            def retry_action():
                try:
                    r = action()
                    return True, r
                except:
                    return False, None

            recovery_result = self.recovery.attempt_recovery(
                reason, current_state, retry_action
            )

            if recovery_result.success:
                # Try action again after recovery
                try:
                    result = action()
                    return True, result, None
                except Exception as e2:
                    return False, None, FailureReason.from_exception(e2)

            return False, None, reason

    # ==================== JOB TRACKING ====================

    def start_job(self, job_id: str, job_type: str = "generic",
                  context: Dict = None) -> JobTrace:
        """Start tracking a job"""
        self._current_job_id = job_id
        self._job_start_time = datetime.now()
        self.performance.reset_job_screenshots(job_id)

        return self.observability.start_job(job_id, job_type, context)

    def end_job(self, success: bool, reason: FailureReason = None):
        """End job tracking"""
        if self._current_job_id:
            self.observability.complete_job(self._current_job_id, success, reason)
            self.performance.reset_job_screenshots(self._current_job_id)

        self._current_job_id = None
        self._job_start_time = None

    # ==================== DIAGNOSTICS ====================

    def get_health(self) -> Dict:
        """Get overall client health"""
        health = {
            'session': self.session.get_health_status(),
            'targets': self.targets.get_status(),
            'performance': self.performance.get_metrics(),
            'observability': self.observability.get_metrics()
        }

        if self.watchdog:
            health['watchdog'] = self.watchdog.get_status_summary()

        return health

    def get_operation_log(self) -> List[Dict]:
        """Get operation log for debugging"""
        # This could aggregate logs from various components
        return []
