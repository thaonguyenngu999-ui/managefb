"""
Navigation Correctness MAX - SPA handling and navigation management

Features:
- Distinguish same-document navigation (hash, SPA route) vs full navigation
- SPA: wait route + wait data fetch + wait render stable
- Guard rails: detect redirect loops, unexpected interstitial pages
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
import time
import re

from .session import CDPSession, CommandResult
from .events import EventEmitter, CDPEvent, EventType, NetworkMonitor
from .waits import WaitEngine, WaitCondition, ConditionType, WaitResult
from .observability import ReasonCode, FailureReason


class NavigationType(Enum):
    """Types of navigation"""
    FULL = auto()           # Full page load
    SAME_DOCUMENT = auto()  # Hash change or History API
    RELOAD = auto()         # Page reload
    BACK_FORWARD = auto()   # History navigation
    FORM_SUBMIT = auto()    # Form submission
    LINK_CLICK = auto()     # Link click
    REDIRECT = auto()       # Server redirect
    SPA_ROUTE = auto()      # Single-page app route change


@dataclass
class NavigationResult:
    """Result from a navigation"""
    success: bool
    navigation_type: NavigationType
    start_url: str
    end_url: str
    elapsed_ms: int
    error: Optional[str] = None
    reason: Optional[FailureReason] = None
    redirects: List[str] = field(default_factory=list)
    is_spa: bool = False


@dataclass
class SPAConfig:
    """Configuration for SPA detection and handling"""
    # Indicators that suggest SPA
    spa_frameworks: List[str] = field(default_factory=lambda: [
        'react', 'vue', 'angular', 'svelte', 'next', 'nuxt'
    ])

    # Elements that indicate SPA is loading
    loading_indicators: List[str] = field(default_factory=lambda: [
        '[data-loading]', '.loading', '.spinner', '[aria-busy="true"]',
        '.skeleton', '[data-skeleton]'
    ])

    # How long to wait for route to stabilize
    route_settle_ms: int = 300

    # How long to wait for data fetch
    data_fetch_timeout_ms: int = 10000

    # How long to wait for render to stabilize
    render_stable_ms: int = 500


class NavigationManager:
    """
    Manages page navigation with SPA awareness

    Key principles:
    - Don't assume navigation is done just because URL changed
    - Wait for data to load and render to stabilize
    - Detect and handle redirect loops
    - Track navigation history for debugging
    """

    def __init__(self, session: CDPSession, waits: WaitEngine,
                 spa_config: SPAConfig = None):
        self._session = session
        self._waits = waits
        self._spa_config = spa_config or SPAConfig()
        self._network_monitor = NetworkMonitor(session.events)

        # State tracking
        self._navigation_history: List[Dict] = []
        self._current_url: str = ""
        self._redirect_count = 0
        self._max_redirects = 10

        # SPA detection
        self._is_spa: Optional[bool] = None

        # Subscribe to navigation events
        session.events.on(EventType.PAGE_FRAME_NAVIGATED, self._on_frame_navigated)
        session.events.on(EventType.PAGE_LOAD_EVENT_FIRED, self._on_load_fired)

    def _on_frame_navigated(self, event: CDPEvent):
        """Track frame navigation"""
        frame = event.data.get('frame', {})
        if frame.get('parentId') is None:  # Main frame
            new_url = frame.get('url', '')
            self._navigation_history.append({
                'type': 'navigated',
                'url': new_url,
                'timestamp': datetime.now().isoformat()
            })
            self._current_url = new_url

    def _on_load_fired(self, event: CDPEvent):
        """Track load events"""
        self._navigation_history.append({
            'type': 'loaded',
            'timestamp': datetime.now().isoformat()
        })

    def navigate(self, url: str, timeout_ms: int = 30000,
                 wait_until: str = 'load') -> NavigationResult:
        """
        Navigate to URL with full handling

        Args:
            url: Target URL
            timeout_ms: Maximum wait time
            wait_until: 'load', 'domcontentloaded', 'networkidle', or 'commit'
        """
        start_time = datetime.now()
        start_url = self._session.get_current_url() or ""
        self._redirect_count = 0

        # Perform navigation
        result = self._session.send_command('Page.navigate', {'url': url})

        if not result.success:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return NavigationResult(
                success=False,
                navigation_type=NavigationType.FULL,
                start_url=start_url,
                end_url=start_url,
                elapsed_ms=elapsed,
                error=f"Navigation command failed: {result.error}",
                reason=FailureReason(
                    code=ReasonCode.NAVIGATION_FAILED,
                    message=result.error or "Navigation failed"
                )
            )

        # Wait based on wait_until strategy
        wait_success = False
        if wait_until == 'commit':
            # Just wait for frame to navigate
            wait_success = True
        elif wait_until == 'domcontentloaded':
            wait_result = self._wait_for_dom_content_loaded(timeout_ms)
            wait_success = wait_result.success
        elif wait_until == 'networkidle':
            wait_result = self._wait_for_network_idle(timeout_ms)
            wait_success = wait_result.success
        else:  # 'load' (default)
            wait_result = self._waits.wait_for_navigation(timeout_ms)
            wait_success = wait_result.success

        # Get final URL
        end_url = self._session.get_current_url() or url

        # Check for redirect loop
        if self._redirect_count > self._max_redirects:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return NavigationResult(
                success=False,
                navigation_type=NavigationType.REDIRECT,
                start_url=start_url,
                end_url=end_url,
                elapsed_ms=elapsed,
                error=f"Redirect loop detected ({self._redirect_count} redirects)",
                reason=FailureReason(
                    code=ReasonCode.REDIRECT_LOOP,
                    message=f"Too many redirects: {self._redirect_count}"
                ),
                redirects=self._get_recent_redirects()
            )

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

        if not wait_success:
            return NavigationResult(
                success=False,
                navigation_type=NavigationType.FULL,
                start_url=start_url,
                end_url=end_url,
                elapsed_ms=elapsed,
                error="Navigation timeout",
                reason=FailureReason(
                    code=ReasonCode.NAVIGATION_TIMEOUT,
                    message=f"Navigation did not complete within {timeout_ms}ms"
                )
            )

        # Detect if this is SPA
        is_spa = self._detect_spa()

        return NavigationResult(
            success=True,
            navigation_type=NavigationType.FULL,
            start_url=start_url,
            end_url=end_url,
            elapsed_ms=elapsed,
            is_spa=is_spa
        )

    def navigate_spa(self, action: Callable, url_pattern: str = None,
                     timeout_ms: int = 30000) -> NavigationResult:
        """
        Navigate within SPA (no full page load)

        Args:
            action: Function that triggers navigation (e.g., click)
            url_pattern: Expected URL pattern after navigation
            timeout_ms: Maximum wait time
        """
        start_time = datetime.now()
        start_url = self._session.get_current_url() or ""

        # Execute the navigation action (e.g., click a link)
        try:
            action()
        except Exception as e:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return NavigationResult(
                success=False,
                navigation_type=NavigationType.SPA_ROUTE,
                start_url=start_url,
                end_url=start_url,
                elapsed_ms=elapsed,
                error=f"Navigation action failed: {str(e)}",
                reason=FailureReason(
                    code=ReasonCode.NAVIGATION_FAILED,
                    message=str(e)
                ),
                is_spa=True
            )

        # Wait for URL to change (if pattern specified)
        if url_pattern:
            url_changed = self._wait_for_url_pattern(url_pattern, timeout_ms)
            if not url_changed:
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                return NavigationResult(
                    success=False,
                    navigation_type=NavigationType.SPA_ROUTE,
                    start_url=start_url,
                    end_url=self._session.get_current_url() or start_url,
                    elapsed_ms=elapsed,
                    error=f"URL did not match pattern: {url_pattern}",
                    reason=FailureReason(
                        code=ReasonCode.SPA_NOT_READY,
                        message=f"Expected URL pattern: {url_pattern}"
                    ),
                    is_spa=True
                )

        # Wait for route to settle
        time.sleep(self._spa_config.route_settle_ms / 1000)

        # Wait for network activity to settle
        remaining = timeout_ms - int((datetime.now() - start_time).total_seconds() * 1000)
        if remaining > 0:
            self._network_monitor.wait_for_idle(min(remaining, self._spa_config.data_fetch_timeout_ms))

        # Wait for render to stabilize (no loading indicators)
        remaining = timeout_ms - int((datetime.now() - start_time).total_seconds() * 1000)
        if remaining > 0:
            self._wait_for_spa_ready(remaining)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        end_url = self._session.get_current_url() or start_url

        return NavigationResult(
            success=True,
            navigation_type=NavigationType.SPA_ROUTE,
            start_url=start_url,
            end_url=end_url,
            elapsed_ms=elapsed,
            is_spa=True
        )

    def _wait_for_dom_content_loaded(self, timeout_ms: int) -> WaitResult:
        """Wait for DOMContentLoaded event"""
        return self._waits.wait_for(
            WaitCondition(type=ConditionType.DOCUMENT_READY),
            timeout_ms=timeout_ms
        )

    def _wait_for_network_idle(self, timeout_ms: int) -> WaitResult:
        """Wait for network to be idle"""
        return self._waits.wait_for_network_idle(timeout_ms)

    def _wait_for_url_pattern(self, pattern: str, timeout_ms: int) -> bool:
        """Wait for URL to match pattern"""
        deadline = datetime.now().timestamp() + (timeout_ms / 1000)

        while datetime.now().timestamp() < deadline:
            current_url = self._session.get_current_url()
            if current_url:
                if pattern in current_url:
                    return True
                try:
                    if re.match(pattern, current_url):
                        return True
                except:
                    pass
            time.sleep(0.1)

        return False

    def _wait_for_spa_ready(self, timeout_ms: int) -> bool:
        """Wait for SPA to finish loading (no loading indicators visible)"""
        deadline = datetime.now().timestamp() + (timeout_ms / 1000)

        while datetime.now().timestamp() < deadline:
            has_loading = False

            for selector in self._spa_config.loading_indicators:
                js = f"""
                    (function() {{
                        let el = document.querySelector('{selector}');
                        if (!el) return false;
                        let style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    }})()
                """
                result = self._session.evaluate_js(js)
                if result.success and result.result:
                    if result.result.get('result', {}).get('value'):
                        has_loading = True
                        break

            if not has_loading:
                # No loading indicators, check if content is stable
                time.sleep(self._spa_config.render_stable_ms / 1000)
                return True

            time.sleep(0.1)

        return False

    def _detect_spa(self) -> bool:
        """Detect if current page is a SPA"""
        if self._is_spa is not None:
            return self._is_spa

        # Check for common SPA framework indicators
        js = """
            (function() {
                // React
                if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__ ||
                    document.querySelector('[data-reactroot]') ||
                    document.querySelector('[data-react-helmet]')) {
                    return 'react';
                }

                // Vue
                if (window.__VUE__ || document.querySelector('[data-v-]')) {
                    return 'vue';
                }

                // Angular
                if (window.ng || document.querySelector('[ng-version]') ||
                    document.querySelector('[_nghost-]')) {
                    return 'angular';
                }

                // Next.js
                if (window.__NEXT_DATA__ || document.querySelector('#__next')) {
                    return 'next';
                }

                // Nuxt
                if (window.__NUXT__ || document.querySelector('#__nuxt')) {
                    return 'nuxt';
                }

                // Generic SPA indicators
                if (document.querySelector('[data-router]') ||
                    document.querySelector('[data-route]')) {
                    return 'generic';
                }

                return null;
            })()
        """

        result = self._session.evaluate_js(js)
        if result.success and result.result:
            framework = result.result.get('result', {}).get('value')
            self._is_spa = framework is not None
            return self._is_spa

        self._is_spa = False
        return False

    def wait_for_navigation_complete(self, timeout_ms: int = 30000) -> NavigationResult:
        """Wait for any pending navigation to complete"""
        start_time = datetime.now()
        start_url = self._session.get_current_url() or ""

        # Wait for page load
        wait_result = self._waits.wait_for_navigation(timeout_ms)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        end_url = self._session.get_current_url() or start_url

        return NavigationResult(
            success=wait_result.success,
            navigation_type=NavigationType.FULL,
            start_url=start_url,
            end_url=end_url,
            elapsed_ms=elapsed,
            error=wait_result.error if not wait_result.success else None
        )

    def detect_unexpected_page(self, expected_patterns: List[str]) -> Optional[str]:
        """
        Check if current page is unexpected (e.g., login page, error page)

        Returns description of unexpected page if found, None otherwise.
        """
        current_url = self._session.get_current_url() or ""

        # Check URL against expected patterns
        matches_expected = False
        for pattern in expected_patterns:
            if pattern in current_url:
                matches_expected = True
                break
            try:
                if re.match(pattern, current_url):
                    matches_expected = True
                    break
            except:
                pass

        if matches_expected:
            return None

        # Check for common unexpected pages
        unexpected_indicators = [
            ('/login', 'Login page'),
            ('/signin', 'Sign-in page'),
            ('/auth', 'Authentication page'),
            ('/error', 'Error page'),
            ('/404', 'Not found page'),
            ('/500', 'Server error page'),
            ('/maintenance', 'Maintenance page'),
            ('/blocked', 'Blocked page'),
            ('/captcha', 'Captcha page'),
            ('/checkpoint', 'Checkpoint page'),
        ]

        for pattern, description in unexpected_indicators:
            if pattern in current_url.lower():
                return description

        return f"Unexpected URL: {current_url}"

    def go_back(self, timeout_ms: int = 10000) -> NavigationResult:
        """Navigate back in history"""
        start_time = datetime.now()
        start_url = self._session.get_current_url() or ""

        result = self._session.send_command('Page.navigateToHistoryEntry', {
            'entryId': -1  # Go back
        })

        # Use history.back() instead
        self._session.evaluate_js('window.history.back()')

        # Wait for navigation
        wait_result = self._waits.wait_for_navigation(timeout_ms)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        end_url = self._session.get_current_url() or start_url

        return NavigationResult(
            success=wait_result.success,
            navigation_type=NavigationType.BACK_FORWARD,
            start_url=start_url,
            end_url=end_url,
            elapsed_ms=elapsed
        )

    def reload(self, timeout_ms: int = 30000, bypass_cache: bool = False) -> NavigationResult:
        """Reload current page"""
        start_time = datetime.now()
        start_url = self._session.get_current_url() or ""

        result = self._session.send_command('Page.reload', {
            'ignoreCache': bypass_cache
        })

        # Wait for load
        wait_result = self._waits.wait_for_navigation(timeout_ms)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

        return NavigationResult(
            success=wait_result.success,
            navigation_type=NavigationType.RELOAD,
            start_url=start_url,
            end_url=start_url,
            elapsed_ms=elapsed
        )

    def _get_recent_redirects(self) -> List[str]:
        """Get recent redirect URLs from history"""
        redirects = []
        for entry in self._navigation_history[-20:]:
            if entry.get('type') == 'navigated':
                redirects.append(entry.get('url', ''))
        return redirects

    def get_navigation_history(self) -> List[Dict]:
        """Get navigation history for debugging"""
        return self._navigation_history.copy()
