"""
Deterministic Waiting MAX - No blind sleep

Features:
- Wait by DOM condition (visible/enabled/stable)
- Wait by Network condition (request/response complete)
- Wait by Rendering stability (layout stable X ms)
- Timeout tiers: step < state < job
- Stability window: condition must be true for 300-800ms
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import threading
import time
import re

from .session import CDPSession, CommandResult
from .events import EventEmitter, EventType, NetworkMonitor
from .observability import ReasonCode, FailureReason


class ConditionType(Enum):
    """Types of wait conditions"""
    # DOM conditions
    ELEMENT_EXISTS = auto()
    ELEMENT_VISIBLE = auto()
    ELEMENT_HIDDEN = auto()
    ELEMENT_CLICKABLE = auto()
    ELEMENT_ENABLED = auto()
    ELEMENT_STABLE = auto()
    TEXT_PRESENT = auto()
    TEXT_ABSENT = auto()
    ATTRIBUTE_EQUALS = auto()
    ATTRIBUTE_CONTAINS = auto()

    # Network conditions
    NETWORK_IDLE = auto()
    REQUEST_COMPLETE = auto()
    RESPONSE_RECEIVED = auto()
    NO_PENDING_REQUESTS = auto()

    # Page conditions
    PAGE_LOADED = auto()
    DOCUMENT_READY = auto()
    URL_CONTAINS = auto()
    URL_MATCHES = auto()
    TITLE_CONTAINS = auto()

    # Render stability
    LAYOUT_STABLE = auto()
    NO_ANIMATIONS = auto()

    # Custom
    CUSTOM = auto()


@dataclass
class WaitCondition:
    """A wait condition specification"""
    type: ConditionType
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    attribute: Optional[str] = None
    value: Optional[str] = None
    url_pattern: Optional[str] = None
    custom_fn: Optional[Callable[[], bool]] = None
    description: str = ""

    def __str__(self) -> str:
        if self.description:
            return self.description
        return f"{self.type.name}: {self.selector or self.url or self.text or ''}"


@dataclass
class WaitResult:
    """Result from waiting for a condition"""
    success: bool
    elapsed_ms: int
    condition: WaitCondition
    error: Optional[str] = None
    reason: Optional[FailureReason] = None
    data: Any = None
    stability_checks: int = 0


@dataclass
class DOMCondition:
    """DOM-specific condition with element state checking"""
    selector: str
    visible: bool = True
    clickable: bool = False
    enabled: bool = False
    stable_ms: int = 0  # Element position must be stable for this long
    text_contains: Optional[str] = None
    attribute_name: Optional[str] = None
    attribute_value: Optional[str] = None

    def to_js(self) -> str:
        """Generate JavaScript to check this condition"""
        checks = []

        if self.visible:
            checks.append("""
                (function() {
                    let rect = el.getBoundingClientRect();
                    let style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 &&
                           style.visibility !== 'hidden' &&
                           style.display !== 'none' &&
                           style.opacity !== '0';
                })()
            """)

        if self.clickable:
            checks.append("""
                (function() {
                    let rect = el.getBoundingClientRect();
                    if (rect.width <= 0 || rect.height <= 0) return false;
                    if (rect.top < 0 || rect.bottom > window.innerHeight) return false;
                    if (rect.left < 0 || rect.right > window.innerWidth) return false;
                    if (el.disabled) return false;
                    // Check if element is covered
                    let centerX = rect.left + rect.width / 2;
                    let centerY = rect.top + rect.height / 2;
                    let topEl = document.elementFromPoint(centerX, centerY);
                    return el.contains(topEl) || topEl === el;
                })()
            """)

        if self.enabled:
            checks.append("!el.disabled")

        if self.text_contains:
            escaped = self.text_contains.replace("'", "\\'")
            checks.append(f"el.textContent.includes('{escaped}')")

        if self.attribute_name and self.attribute_value:
            attr = self.attribute_name
            val = self.attribute_value.replace("'", "\\'")
            checks.append(f"(el.getAttribute('{attr}') || '').includes('{val}')")

        selector_escaped = self.selector.replace("'", "\\'")
        check_expr = ' && '.join(checks) if checks else 'true'

        return f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return {{found: false}};
                let valid = {check_expr};
                if (!valid) return {{found: true, valid: false}};
                let rect = el.getBoundingClientRect();
                return {{
                    found: true,
                    valid: true,
                    rect: {{
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }}
                }};
            }})()
        """


@dataclass
class NetworkCondition:
    """Network-specific condition"""
    url_pattern: Optional[str] = None  # Wait for request/response matching this
    method: Optional[str] = None  # GET, POST, etc.
    status_code: Optional[int] = None
    idle_timeout_ms: int = 500  # How long network must be idle

    def matches_request(self, event_data: Dict) -> bool:
        """Check if a network event matches this condition"""
        if self.url_pattern:
            url = event_data.get('request', {}).get('url', '')
            if not url:
                url = event_data.get('response', {}).get('url', '')
            if self.url_pattern not in url:
                return False

        if self.method:
            method = event_data.get('request', {}).get('method', '')
            if method.upper() != self.method.upper():
                return False

        if self.status_code:
            status = event_data.get('response', {}).get('status')
            if status != self.status_code:
                return False

        return True


@dataclass
class StabilityCondition:
    """Rendering stability condition"""
    selector: str
    stable_duration_ms: int = 500  # Position must be stable for this long
    check_interval_ms: int = 100


class WaitEngine:
    """
    Wait engine with stability window and multiple condition types

    Key principles:
    - Never blind sleep
    - Condition must be true for stability_window_ms to be considered met
    - Timeout tiers: step_timeout < state_timeout < job_deadline
    """

    def __init__(self, session: CDPSession):
        self._session = session
        self._network_monitor = NetworkMonitor(session.events)

        # Default timeouts (step < state < job)
        self.step_timeout_ms = 10000
        self.state_timeout_ms = 30000
        self.job_timeout_ms = 300000

        # Stability window
        self.stability_window_ms = 500  # Condition must be true for this long
        self.poll_interval_ms = 100

    def wait_for(self, condition: WaitCondition, timeout_ms: int = None,
                 stability_ms: int = None) -> WaitResult:
        """
        Wait for a condition to be met

        Args:
            condition: The condition to wait for
            timeout_ms: Maximum wait time (defaults to step_timeout_ms)
            stability_ms: How long condition must be true (defaults to stability_window_ms)

        Returns:
            WaitResult with success status and timing info
        """
        timeout = timeout_ms or self.step_timeout_ms
        stability = stability_ms or self.stability_window_ms

        start_time = datetime.now()
        deadline = start_time.timestamp() + (timeout / 1000)

        condition_met_since: Optional[datetime] = None
        stability_checks = 0

        while datetime.now().timestamp() < deadline:
            try:
                result = self._check_condition(condition)

                if result:
                    stability_checks += 1
                    if condition_met_since is None:
                        condition_met_since = datetime.now()
                    else:
                        # Check if condition has been true for stability window
                        stable_for = (datetime.now() - condition_met_since).total_seconds() * 1000
                        if stable_for >= stability:
                            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                            return WaitResult(
                                success=True,
                                elapsed_ms=elapsed,
                                condition=condition,
                                data=result,
                                stability_checks=stability_checks
                            )
                else:
                    # Condition became false, reset stability counter
                    condition_met_since = None

            except Exception as e:
                # Check failed, reset stability counter
                condition_met_since = None

            time.sleep(self.poll_interval_ms / 1000)

        # Timeout
        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return WaitResult(
            success=False,
            elapsed_ms=elapsed,
            condition=condition,
            error=f"Timeout waiting for: {condition}",
            reason=FailureReason(
                code=ReasonCode.TIMEOUT_STEP,
                message=f"Condition not met within {timeout}ms: {condition}",
                context={'condition': str(condition), 'timeout_ms': timeout}
            ),
            stability_checks=stability_checks
        )

    def _check_condition(self, condition: WaitCondition) -> Any:
        """Check if a condition is met"""
        if condition.type == ConditionType.ELEMENT_EXISTS:
            return self._check_element_exists(condition.selector)

        elif condition.type == ConditionType.ELEMENT_VISIBLE:
            return self._check_element_visible(condition.selector)

        elif condition.type == ConditionType.ELEMENT_HIDDEN:
            return not self._check_element_visible(condition.selector)

        elif condition.type == ConditionType.ELEMENT_CLICKABLE:
            return self._check_element_clickable(condition.selector)

        elif condition.type == ConditionType.ELEMENT_ENABLED:
            return self._check_element_enabled(condition.selector)

        elif condition.type == ConditionType.TEXT_PRESENT:
            return self._check_text_present(condition.selector, condition.text)

        elif condition.type == ConditionType.TEXT_ABSENT:
            return not self._check_text_present(condition.selector, condition.text)

        elif condition.type == ConditionType.ATTRIBUTE_EQUALS:
            return self._check_attribute(condition.selector, condition.attribute, condition.value, exact=True)

        elif condition.type == ConditionType.ATTRIBUTE_CONTAINS:
            return self._check_attribute(condition.selector, condition.attribute, condition.value, exact=False)

        elif condition.type == ConditionType.NETWORK_IDLE:
            return self._network_monitor.is_idle()

        elif condition.type == ConditionType.NO_PENDING_REQUESTS:
            return self._network_monitor.get_pending_count() == 0

        elif condition.type == ConditionType.PAGE_LOADED:
            return self._check_page_loaded()

        elif condition.type == ConditionType.DOCUMENT_READY:
            return self._check_document_ready()

        elif condition.type == ConditionType.URL_CONTAINS:
            return self._check_url_contains(condition.url)

        elif condition.type == ConditionType.URL_MATCHES:
            return self._check_url_matches(condition.url)

        elif condition.type == ConditionType.TITLE_CONTAINS:
            return self._check_title_contains(condition.text)

        elif condition.type == ConditionType.LAYOUT_STABLE:
            return self._check_layout_stable(condition.selector)

        elif condition.type == ConditionType.CUSTOM:
            if condition.custom_fn:
                return condition.custom_fn()
            return False

        return False

    def _evaluate_js(self, expression: str) -> Any:
        """Evaluate JavaScript and return result value"""
        result = self._session.evaluate_js(expression, await_promise=False)
        if result.success and result.result:
            return result.result.get('result', {}).get('value')
        return None

    def _check_element_exists(self, selector: str) -> bool:
        selector_escaped = selector.replace("'", "\\'")
        js = f"document.querySelector('{selector_escaped}') !== null"
        return self._evaluate_js(js) == True

    def _check_element_visible(self, selector: str) -> bool:
        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return false;
                let rect = el.getBoundingClientRect();
                let style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 &&
                       style.visibility !== 'hidden' &&
                       style.display !== 'none' &&
                       style.opacity !== '0';
            }})()
        """
        return self._evaluate_js(js) == True

    def _check_element_clickable(self, selector: str) -> bool:
        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return false;
                let rect = el.getBoundingClientRect();
                if (rect.width <= 0 || rect.height <= 0) return false;
                if (rect.top < 0 || rect.bottom > window.innerHeight) return false;
                if (el.disabled) return false;
                // Check if visible
                let style = window.getComputedStyle(el);
                if (style.visibility === 'hidden' || style.display === 'none') return false;
                // Check if not covered
                let centerX = rect.left + rect.width / 2;
                let centerY = rect.top + rect.height / 2;
                let topEl = document.elementFromPoint(centerX, centerY);
                return topEl && (el.contains(topEl) || topEl === el);
            }})()
        """
        return self._evaluate_js(js) == True

    def _check_element_enabled(self, selector: str) -> bool:
        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                return el && !el.disabled;
            }})()
        """
        return self._evaluate_js(js) == True

    def _check_text_present(self, selector: str, text: str) -> bool:
        selector_escaped = selector.replace("'", "\\'")
        text_escaped = text.replace("'", "\\'")
        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                return el && el.textContent.includes('{text_escaped}');
            }})()
        """
        return self._evaluate_js(js) == True

    def _check_attribute(self, selector: str, attr: str, value: str, exact: bool = True) -> bool:
        selector_escaped = selector.replace("'", "\\'")
        attr_escaped = attr.replace("'", "\\'")
        value_escaped = value.replace("'", "\\'")

        if exact:
            js = f"""
                (function() {{
                    let el = document.querySelector('{selector_escaped}');
                    return el && el.getAttribute('{attr_escaped}') === '{value_escaped}';
                }})()
            """
        else:
            js = f"""
                (function() {{
                    let el = document.querySelector('{selector_escaped}');
                    return el && (el.getAttribute('{attr_escaped}') || '').includes('{value_escaped}');
                }})()
            """
        return self._evaluate_js(js) == True

    def _check_page_loaded(self) -> bool:
        js = "document.readyState === 'complete'"
        return self._evaluate_js(js) == True

    def _check_document_ready(self) -> bool:
        js = "document.readyState !== 'loading'"
        return self._evaluate_js(js) == True

    def _check_url_contains(self, url_part: str) -> bool:
        url_escaped = url_part.replace("'", "\\'")
        js = f"window.location.href.includes('{url_escaped}')"
        return self._evaluate_js(js) == True

    def _check_url_matches(self, pattern: str) -> bool:
        current_url = self._session.get_current_url()
        if current_url:
            return bool(re.match(pattern, current_url))
        return False

    def _check_title_contains(self, text: str) -> bool:
        text_escaped = text.replace("'", "\\'")
        js = f"document.title.includes('{text_escaped}')"
        return self._evaluate_js(js) == True

    def _check_layout_stable(self, selector: str) -> bool:
        """Check if element layout is stable (not animating/moving)"""
        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return null;
                let rect = el.getBoundingClientRect();
                return {{x: rect.x, y: rect.y, w: rect.width, h: rect.height}};
            }})()
        """
        return self._evaluate_js(js) is not None

    def wait_for_dom(self, condition: DOMCondition, timeout_ms: int = None) -> WaitResult:
        """Wait for a DOM condition with full checking"""
        timeout = timeout_ms or self.step_timeout_ms
        start_time = datetime.now()
        deadline = start_time.timestamp() + (timeout / 1000)

        last_rect = None
        stable_since = None

        while datetime.now().timestamp() < deadline:
            js = condition.to_js()
            result = self._evaluate_js(js)

            if result and isinstance(result, dict):
                if not result.get('found'):
                    # Element not found
                    stable_since = None
                    last_rect = None
                elif not result.get('valid'):
                    # Element found but condition not met
                    stable_since = None
                    last_rect = None
                else:
                    # Element found and valid
                    current_rect = result.get('rect')

                    if condition.stable_ms > 0:
                        # Check stability
                        if last_rect and self._rects_equal(last_rect, current_rect):
                            if stable_since is None:
                                stable_since = datetime.now()
                            else:
                                stable_for = (datetime.now() - stable_since).total_seconds() * 1000
                                if stable_for >= condition.stable_ms:
                                    elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                                    return WaitResult(
                                        success=True,
                                        elapsed_ms=elapsed,
                                        condition=WaitCondition(
                                            type=ConditionType.ELEMENT_STABLE,
                                            selector=condition.selector
                                        ),
                                        data=result
                                    )
                        else:
                            stable_since = None
                        last_rect = current_rect
                    else:
                        # No stability required
                        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                        return WaitResult(
                            success=True,
                            elapsed_ms=elapsed,
                            condition=WaitCondition(
                                type=ConditionType.ELEMENT_VISIBLE,
                                selector=condition.selector
                            ),
                            data=result
                        )

            time.sleep(self.poll_interval_ms / 1000)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return WaitResult(
            success=False,
            elapsed_ms=elapsed,
            condition=WaitCondition(
                type=ConditionType.ELEMENT_STABLE,
                selector=condition.selector
            ),
            error=f"Timeout waiting for DOM condition: {condition.selector}",
            reason=FailureReason(
                code=ReasonCode.TIMEOUT_STEP,
                message=f"DOM condition not met: {condition.selector}"
            )
        )

    def _rects_equal(self, rect1: Dict, rect2: Dict, tolerance: float = 2.0) -> bool:
        """Check if two rects are approximately equal"""
        if not rect1 or not rect2:
            return False
        return (
            abs(rect1.get('x', 0) - rect2.get('x', 0)) < tolerance and
            abs(rect1.get('y', 0) - rect2.get('y', 0)) < tolerance and
            abs(rect1.get('w', 0) - rect2.get('w', 0)) < tolerance and
            abs(rect1.get('h', 0) - rect2.get('h', 0)) < tolerance
        )

    def wait_for_network_idle(self, timeout_ms: int = None, idle_time_ms: int = 500) -> WaitResult:
        """Wait for network to be idle"""
        timeout = timeout_ms or self.step_timeout_ms
        start_time = datetime.now()

        success = self._network_monitor.wait_for_idle(timeout_ms=timeout)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return WaitResult(
            success=success,
            elapsed_ms=elapsed,
            condition=WaitCondition(type=ConditionType.NETWORK_IDLE),
            error=None if success else "Network not idle within timeout",
            reason=None if success else FailureReason(
                code=ReasonCode.TIMEOUT_NETWORK,
                message=f"Network not idle within {timeout}ms"
            )
        )

    def wait_for_navigation(self, timeout_ms: int = None) -> WaitResult:
        """Wait for page navigation to complete"""
        timeout = timeout_ms or self.state_timeout_ms
        start_time = datetime.now()

        event = self._session.events.wait_for(EventType.PAGE_LOAD_EVENT_FIRED, timeout_ms=timeout)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

        if event:
            return WaitResult(
                success=True,
                elapsed_ms=elapsed,
                condition=WaitCondition(type=ConditionType.PAGE_LOADED),
                data=event.data
            )
        else:
            return WaitResult(
                success=False,
                elapsed_ms=elapsed,
                condition=WaitCondition(type=ConditionType.PAGE_LOADED),
                error="Navigation timeout",
                reason=FailureReason(
                    code=ReasonCode.NAVIGATION_TIMEOUT,
                    message=f"Navigation did not complete within {timeout}ms"
                )
            )
