"""
Action Layer MAX - Actions with semantics

Every action has:
- Precondition: element exists + interactable
- Postcondition: UI state changed as expected
- Idempotent actions: clicking again doesn't break things
- Atomicity: complex actions broken into verifiable steps
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import time

from .session import CDPSession, CommandResult
from .selectors import SelectorEngine, Locator, ElementHandle
from .waits import WaitEngine, WaitCondition, ConditionType, WaitResult, DOMCondition
from .observability import ReasonCode, FailureReason, get_observability


class ActionType(Enum):
    """Types of actions"""
    CLICK = auto()
    DOUBLE_CLICK = auto()
    RIGHT_CLICK = auto()
    TYPE = auto()
    CLEAR = auto()
    SELECT = auto()
    CHECK = auto()
    UNCHECK = auto()
    HOVER = auto()
    SCROLL_TO = auto()
    DRAG_DROP = auto()
    UPLOAD = auto()
    FOCUS = auto()
    BLUR = auto()


@dataclass
class Precondition:
    """Precondition that must be true before action"""
    check: Callable[[], bool]
    description: str
    failure_reason: ReasonCode = ReasonCode.PRECONDITION_FAILED


@dataclass
class Postcondition:
    """Postcondition that must be true after action"""
    check: Callable[[], bool]
    description: str
    failure_reason: ReasonCode = ReasonCode.POSTCONDITION_FAILED
    timeout_ms: int = 5000


@dataclass
class ActionResult:
    """Result from executing an action"""
    success: bool
    action_type: ActionType
    locator: Optional[Locator] = None
    elapsed_ms: int = 0
    error: Optional[str] = None
    reason: Optional[FailureReason] = None
    data: Any = None
    precondition_passed: bool = True
    postcondition_passed: bool = True


class IdempotentGuard:
    """
    Guard to make actions idempotent

    Checks if action already done before executing.
    """

    def __init__(self, check_fn: Callable[[], bool], description: str = ""):
        self.check_fn = check_fn
        self.description = description

    def is_already_done(self) -> bool:
        """Check if action effect already exists"""
        try:
            return self.check_fn()
        except:
            return False


class AtomicAction:
    """
    An atomic action with its pre/postconditions

    Complex actions are broken into AtomicActions with verification at each step.
    """

    def __init__(self, name: str, execute_fn: Callable[[], bool],
                 precondition: Optional[Precondition] = None,
                 postcondition: Optional[Postcondition] = None,
                 idempotent_guard: Optional[IdempotentGuard] = None):
        self.name = name
        self.execute_fn = execute_fn
        self.precondition = precondition
        self.postcondition = postcondition
        self.idempotent_guard = idempotent_guard


class ActionExecutor:
    """
    Executes actions with MAX semantics

    Every action:
    1. Checks precondition (element ready)
    2. Checks idempotent guard (skip if already done)
    3. Executes action
    4. Verifies postcondition (UI changed)
    """

    def __init__(self, session: CDPSession, selectors: SelectorEngine, waits: WaitEngine):
        self._session = session
        self._selectors = selectors
        self._waits = waits
        self._obs = get_observability()

    def click(self, locator: Locator,
              postcondition: Postcondition = None,
              idempotent_guard: IdempotentGuard = None) -> ActionResult:
        """
        Click element with full verification

        Precondition: Element is visible and clickable
        Postcondition: Custom or default (element state changed)
        """
        start_time = datetime.now()

        # Check idempotent guard
        if idempotent_guard and idempotent_guard.is_already_done():
            return ActionResult(
                success=True,
                action_type=ActionType.CLICK,
                locator=locator,
                elapsed_ms=0,
                reason=FailureReason(
                    code=ReasonCode.SKIPPED_IDEMPOTENT,
                    message=idempotent_guard.description or "Action already done"
                )
            )

        # Precondition: Element must be clickable
        dom_condition = DOMCondition(
            selector=locator.to_selector(),
            visible=True,
            clickable=True
        )
        wait_result = self._waits.wait_for_dom(dom_condition, timeout_ms=locator.timeout_ms)

        if not wait_result.success:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                locator=locator,
                elapsed_ms=elapsed,
                error="Precondition failed: element not clickable",
                reason=FailureReason(
                    code=ReasonCode.ELEMENT_NOT_CLICKABLE,
                    message=f"Element not clickable: {locator.to_selector()}"
                ),
                precondition_passed=False
            )

        # Execute click
        selector = locator.to_selector()
        selector_escaped = selector.replace("'", "\\'")

        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return {{success: false, error: 'not found'}};

                // Get element center
                let rect = el.getBoundingClientRect();
                let centerX = rect.left + rect.width / 2;
                let centerY = rect.top + rect.height / 2;

                // Check if covered
                let topEl = document.elementFromPoint(centerX, centerY);
                if (!el.contains(topEl) && topEl !== el) {{
                    return {{success: false, error: 'covered by ' + topEl.tagName}};
                }}

                // Click
                el.click();
                return {{success: true}};
            }})()
        """

        result = self._session.evaluate_js(js)
        if not result.success or not result.result:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                locator=locator,
                elapsed_ms=elapsed,
                error="Click execution failed",
                reason=FailureReason(
                    code=ReasonCode.CDP_COMMAND_FAILED,
                    message="Click command failed"
                )
            )

        click_result = result.result.get('result', {}).get('value', {})
        if not click_result.get('success'):
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                locator=locator,
                elapsed_ms=elapsed,
                error=click_result.get('error', 'Click failed'),
                reason=FailureReason(
                    code=ReasonCode.ELEMENT_COVERED if 'covered' in click_result.get('error', '') else ReasonCode.ELEMENT_NOT_CLICKABLE,
                    message=click_result.get('error', 'Click failed')
                )
            )

        # Postcondition check
        if postcondition:
            deadline = datetime.now().timestamp() + (postcondition.timeout_ms / 1000)
            postcondition_met = False

            while datetime.now().timestamp() < deadline:
                try:
                    if postcondition.check():
                        postcondition_met = True
                        break
                except:
                    pass
                time.sleep(0.1)

            if not postcondition_met:
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                return ActionResult(
                    success=False,
                    action_type=ActionType.CLICK,
                    locator=locator,
                    elapsed_ms=elapsed,
                    error=f"Postcondition failed: {postcondition.description}",
                    reason=FailureReason(
                        code=postcondition.failure_reason,
                        message=postcondition.description
                    ),
                    postcondition_passed=False
                )

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return ActionResult(
            success=True,
            action_type=ActionType.CLICK,
            locator=locator,
            elapsed_ms=elapsed
        )

    def type_text(self, locator: Locator, text: str, clear: bool = True,
                  postcondition: Postcondition = None) -> ActionResult:
        """
        Type text into input with verification

        Precondition: Element is visible and focusable
        Postcondition: Text appears in input
        """
        start_time = datetime.now()

        # Precondition: Element must be visible
        dom_condition = DOMCondition(
            selector=locator.to_selector(),
            visible=True
        )
        wait_result = self._waits.wait_for_dom(dom_condition, timeout_ms=locator.timeout_ms)

        if not wait_result.success:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                locator=locator,
                elapsed_ms=elapsed,
                error="Precondition failed: element not visible",
                reason=FailureReason(
                    code=ReasonCode.ELEMENT_NOT_VISIBLE,
                    message=f"Element not visible: {locator.to_selector()}"
                ),
                precondition_passed=False
            )

        # Execute type
        selector = locator.to_selector()
        selector_escaped = selector.replace("'", "\\'")
        text_escaped = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("`", "\\`")

        # Step 1: Focus element và check type
        focus_js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return {{success: false, error: 'not found'}};

                el.focus();

                let isContentEditable = el.getAttribute('contenteditable') === 'true';

                if (isContentEditable) {{
                    if ({str(clear).lower()}) {{
                        el.innerHTML = '';
                    }}
                    return {{success: true, isContentEditable: true}};
                }} else {{
                    if ({str(clear).lower()}) {{
                        el.value = '';
                    }}
                    el.value += '{text_escaped}';
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return {{success: true, isContentEditable: false, value: el.value}};
                }}
            }})()
        """

        result = self._session.evaluate_js(focus_js)
        if result.success and result.result:
            type_result = result.result.get('result', {}).get('value', {})
            if type_result.get('success') and type_result.get('isContentEditable'):
                # Dùng CDP Input.insertText cho contenteditable (hoạt động với Lexical editor)
                try:
                    self._session.send_command('Input.insertText', {'text': text})
                except Exception as e:
                    print(f"[Actions] Input.insertText error: {e}")
                    # Fallback to JS execCommand
                    fallback_js = f"document.execCommand('insertText', false, '{text_escaped}');"
                    self._session.evaluate_js(fallback_js)

        # Verify type result
        verify_js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return {{success: false}};
                return {{success: true, value: el.value || el.textContent}};
            }})()
        """
        result = self._session.evaluate_js(verify_js)
        if not result.success or not result.result:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                locator=locator,
                elapsed_ms=elapsed,
                error="Type execution failed",
                reason=FailureReason(
                    code=ReasonCode.CDP_COMMAND_FAILED,
                    message="Type command failed"
                )
            )

        type_result = result.result.get('result', {}).get('value', {})
        if not type_result.get('success'):
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                locator=locator,
                elapsed_ms=elapsed,
                error=type_result.get('error', 'Type failed'),
                reason=FailureReason(
                    code=ReasonCode.ELEMENT_NOT_FOUND,
                    message=type_result.get('error', 'Type failed')
                )
            )

        # Default postcondition: text should be in element
        if postcondition is None:
            postcondition = Postcondition(
                check=lambda: self._verify_text_in_element(selector, text),
                description=f"Text '{text[:20]}...' should be in element",
                timeout_ms=2000
            )

        if postcondition:
            deadline = datetime.now().timestamp() + (postcondition.timeout_ms / 1000)
            postcondition_met = False

            while datetime.now().timestamp() < deadline:
                try:
                    if postcondition.check():
                        postcondition_met = True
                        break
                except:
                    pass
                time.sleep(0.1)

            if not postcondition_met:
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                return ActionResult(
                    success=False,
                    action_type=ActionType.TYPE,
                    locator=locator,
                    elapsed_ms=elapsed,
                    error=f"Postcondition failed: {postcondition.description}",
                    reason=FailureReason(
                        code=postcondition.failure_reason,
                        message=postcondition.description
                    ),
                    postcondition_passed=False
                )

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
        return ActionResult(
            success=True,
            action_type=ActionType.TYPE,
            locator=locator,
            elapsed_ms=elapsed,
            data={'typed_text': text}
        )

    def _verify_text_in_element(self, selector: str, text: str) -> bool:
        """Verify text appears in element"""
        selector_escaped = selector.replace("'", "\\'")
        text_escaped = text.replace("'", "\\'")

        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return false;
                let content = el.value || el.textContent || '';
                return content.includes('{text_escaped}');
            }})()
        """

        result = self._session.evaluate_js(js)
        if result.success and result.result:
            return result.result.get('result', {}).get('value', False)
        return False

    def scroll_to(self, locator: Locator) -> ActionResult:
        """Scroll element into view"""
        start_time = datetime.now()

        # Wait for element to exist
        wait_result = self._waits.wait_for(
            WaitCondition(type=ConditionType.ELEMENT_EXISTS, selector=locator.to_selector()),
            timeout_ms=locator.timeout_ms
        )

        if not wait_result.success:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL_TO,
                locator=locator,
                elapsed_ms=elapsed,
                error="Element not found",
                reason=FailureReason(
                    code=ReasonCode.ELEMENT_NOT_FOUND,
                    message=f"Element not found: {locator.to_selector()}"
                )
            )

        selector = locator.to_selector()
        selector_escaped = selector.replace("'", "\\'")

        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return false;
                el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                return true;
            }})()
        """

        result = self._session.evaluate_js(js)

        # Wait for scroll to complete
        time.sleep(0.3)

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

        if result.success and result.result and result.result.get('result', {}).get('value'):
            return ActionResult(
                success=True,
                action_type=ActionType.SCROLL_TO,
                locator=locator,
                elapsed_ms=elapsed
            )

        return ActionResult(
            success=False,
            action_type=ActionType.SCROLL_TO,
            locator=locator,
            elapsed_ms=elapsed,
            error="Scroll failed"
        )

    def hover(self, locator: Locator) -> ActionResult:
        """Hover over element using CDP Input.dispatchMouseEvent"""
        start_time = datetime.now()

        # Get element position
        selector = locator.to_selector()
        selector_escaped = selector.replace("'", "\\'")

        js = f"""
            (function() {{
                let el = document.querySelector('{selector_escaped}');
                if (!el) return null;
                let rect = el.getBoundingClientRect();
                return {{
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2
                }};
            }})()
        """

        result = self._session.evaluate_js(js)
        if not result.success or not result.result:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.HOVER,
                locator=locator,
                elapsed_ms=elapsed,
                error="Element not found"
            )

        pos = result.result.get('result', {}).get('value')
        if not pos:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                success=False,
                action_type=ActionType.HOVER,
                locator=locator,
                elapsed_ms=elapsed,
                error="Could not get element position"
            )

        # Move mouse to element
        mouse_result = self._session.send_command('Input.dispatchMouseEvent', {
            'type': 'mouseMoved',
            'x': pos['x'],
            'y': pos['y']
        })

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

        if mouse_result.success:
            return ActionResult(
                success=True,
                action_type=ActionType.HOVER,
                locator=locator,
                elapsed_ms=elapsed
            )

        return ActionResult(
            success=False,
            action_type=ActionType.HOVER,
            locator=locator,
            elapsed_ms=elapsed,
            error="Mouse move failed"
        )

    def execute_atomic_sequence(self, actions: List[AtomicAction]) -> Tuple[bool, List[ActionResult]]:
        """
        Execute a sequence of atomic actions

        Each action is verified before proceeding to next.
        """
        results = []

        for action in actions:
            start_time = datetime.now()

            # Check idempotent guard
            if action.idempotent_guard and action.idempotent_guard.is_already_done():
                results.append(ActionResult(
                    success=True,
                    action_type=ActionType.CLICK,  # Generic
                    elapsed_ms=0,
                    reason=FailureReason(
                        code=ReasonCode.SKIPPED_IDEMPOTENT,
                        message=f"{action.name}: Already done"
                    )
                ))
                continue

            # Check precondition
            if action.precondition:
                try:
                    if not action.precondition.check():
                        results.append(ActionResult(
                            success=False,
                            action_type=ActionType.CLICK,
                            elapsed_ms=0,
                            error=f"Precondition failed: {action.precondition.description}",
                            reason=FailureReason(
                                code=action.precondition.failure_reason,
                                message=action.precondition.description
                            ),
                            precondition_passed=False
                        ))
                        return False, results
                except Exception as e:
                    results.append(ActionResult(
                        success=False,
                        action_type=ActionType.CLICK,
                        elapsed_ms=0,
                        error=f"Precondition check error: {str(e)}",
                        precondition_passed=False
                    ))
                    return False, results

            # Execute action
            try:
                success = action.execute_fn()
            except Exception as e:
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                results.append(ActionResult(
                    success=False,
                    action_type=ActionType.CLICK,
                    elapsed_ms=elapsed,
                    error=f"Action failed: {str(e)}"
                ))
                return False, results

            if not success:
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                results.append(ActionResult(
                    success=False,
                    action_type=ActionType.CLICK,
                    elapsed_ms=elapsed,
                    error=f"Action {action.name} returned false"
                ))
                return False, results

            # Check postcondition
            if action.postcondition:
                deadline = datetime.now().timestamp() + (action.postcondition.timeout_ms / 1000)
                postcondition_met = False

                while datetime.now().timestamp() < deadline:
                    try:
                        if action.postcondition.check():
                            postcondition_met = True
                            break
                    except:
                        pass
                    time.sleep(0.1)

                if not postcondition_met:
                    elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                    results.append(ActionResult(
                        success=False,
                        action_type=ActionType.CLICK,
                        elapsed_ms=elapsed,
                        error=f"Postcondition failed: {action.postcondition.description}",
                        reason=FailureReason(
                            code=action.postcondition.failure_reason,
                            message=action.postcondition.description
                        ),
                        postcondition_passed=False
                    ))
                    return False, results

            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            results.append(ActionResult(
                success=True,
                action_type=ActionType.CLICK,
                elapsed_ms=elapsed
            ))

        return True, results
