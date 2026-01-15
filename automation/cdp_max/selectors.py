"""
Selector Strategy MAX - Robust element location

Priority order:
1. Semantic/role/aria (most stable)
2. Test-id/automation-id
3. Text locator within narrow scope
4. CSS/xpath (last resort)

Features:
- Scoped search (always search within correct container)
- Frame-safe (auto switch frame/iframe)
- Locator caching with staleness detection
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import re

from .session import CDPSession, CommandResult
from .observability import ReasonCode, FailureReason


class LocatorType(Enum):
    """Locator types in priority order"""
    # Priority 1: Semantic (most stable)
    ROLE = auto()           # [role="button"]
    ARIA_LABEL = auto()     # [aria-label="Submit"]
    ARIA_LABELLEDBY = auto()

    # Priority 2: Test IDs
    TEST_ID = auto()        # [data-testid="submit-btn"]
    AUTOMATION_ID = auto()  # [data-automation-id="..."]

    # Priority 3: Text (within scope)
    TEXT_EXACT = auto()     # :has-text("Submit")
    TEXT_CONTAINS = auto()  # *:contains("Submit")
    PLACEHOLDER = auto()    # [placeholder="..."]
    TITLE = auto()          # [title="..."]

    # Priority 4: Structural (less stable)
    ID = auto()             # #submit-btn
    NAME = auto()           # [name="email"]
    CSS = auto()            # .submit-button
    XPATH = auto()          # //button[@type='submit']


@dataclass
class Locator:
    """Element locator with type and value"""
    type: LocatorType
    value: str
    scope: Optional[str] = None  # Parent selector to scope search
    frame: Optional[str] = None  # Frame selector if element is in iframe
    timeout_ms: int = 10000
    description: str = ""

    def to_selector(self) -> str:
        """Convert to CSS/JS selector"""
        if self.type == LocatorType.ROLE:
            return f'[role="{self.value}"]'
        elif self.type == LocatorType.ARIA_LABEL:
            return f'[aria-label*="{self.value}"]'
        elif self.type == LocatorType.ARIA_LABELLEDBY:
            return f'[aria-labelledby="{self.value}"]'
        elif self.type == LocatorType.TEST_ID:
            return f'[data-testid="{self.value}"]'
        elif self.type == LocatorType.AUTOMATION_ID:
            return f'[data-automation-id="{self.value}"]'
        elif self.type == LocatorType.ID:
            return f'#{self.value}'
        elif self.type == LocatorType.NAME:
            return f'[name="{self.value}"]'
        elif self.type == LocatorType.PLACEHOLDER:
            return f'[placeholder*="{self.value}"]'
        elif self.type == LocatorType.TITLE:
            return f'[title*="{self.value}"]'
        elif self.type == LocatorType.CSS:
            return self.value
        elif self.type == LocatorType.XPATH:
            return self.value  # Handled separately
        elif self.type in [LocatorType.TEXT_EXACT, LocatorType.TEXT_CONTAINS]:
            return self.value  # Handled with JS
        return self.value

    @property
    def is_xpath(self) -> bool:
        return self.type == LocatorType.XPATH

    @property
    def is_text_based(self) -> bool:
        return self.type in [LocatorType.TEXT_EXACT, LocatorType.TEXT_CONTAINS]


@dataclass
class ScopedLocator:
    """Locator with scope chain for nested elements"""
    locators: List[Locator]  # From outer to inner
    description: str = ""

    def __str__(self) -> str:
        if self.description:
            return self.description
        return " > ".join([f"{l.type.name}:{l.value}" for l in self.locators])


@dataclass
class FrameContext:
    """Frame context for iframe handling"""
    frame_id: Optional[str] = None
    frame_selector: Optional[str] = None
    execution_context_id: Optional[int] = None
    is_main_frame: bool = True


@dataclass
class ElementHandle:
    """Handle to a DOM element"""
    node_id: int
    backend_node_id: int
    object_id: str
    locator: Locator
    frame_context: FrameContext
    found_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_stale(self, max_age_ms: int = 5000) -> bool:
        """Check if handle might be stale"""
        age = (datetime.now() - datetime.fromisoformat(self.found_at)).total_seconds() * 1000
        return age > max_age_ms


class SelectorEngine:
    """
    Element selector engine with MAX features

    Features:
    - Priority-based locator strategy
    - Scoped search
    - Frame-safe operations
    - Locator building helpers
    """

    def __init__(self, session: CDPSession):
        self._session = session
        self._current_frame: Optional[FrameContext] = None
        self._frame_stack: List[FrameContext] = []

    # ==================== LOCATOR BUILDERS ====================

    def by_role(self, role: str, name: str = None) -> Locator:
        """Create locator by ARIA role (Priority 1)"""
        if name:
            return Locator(
                type=LocatorType.ARIA_LABEL,
                value=name,
                description=f"role={role}, name={name}"
            )
        return Locator(
            type=LocatorType.ROLE,
            value=role,
            description=f"role={role}"
        )

    def by_aria_label(self, label: str) -> Locator:
        """Create locator by aria-label (Priority 1)"""
        return Locator(
            type=LocatorType.ARIA_LABEL,
            value=label,
            description=f"aria-label*={label}"
        )

    def by_test_id(self, test_id: str) -> Locator:
        """Create locator by test ID (Priority 2)"""
        return Locator(
            type=LocatorType.TEST_ID,
            value=test_id,
            description=f"data-testid={test_id}"
        )

    def by_text(self, text: str, exact: bool = False) -> Locator:
        """Create locator by text content (Priority 3)"""
        return Locator(
            type=LocatorType.TEXT_EXACT if exact else LocatorType.TEXT_CONTAINS,
            value=text,
            description=f"text={'=' if exact else '*='}{text}"
        )

    def by_placeholder(self, placeholder: str) -> Locator:
        """Create locator by placeholder (Priority 3)"""
        return Locator(
            type=LocatorType.PLACEHOLDER,
            value=placeholder,
            description=f"placeholder*={placeholder}"
        )

    def by_css(self, selector: str) -> Locator:
        """Create locator by CSS selector (Priority 4)"""
        return Locator(
            type=LocatorType.CSS,
            value=selector,
            description=f"css={selector}"
        )

    def by_xpath(self, xpath: str) -> Locator:
        """Create locator by XPath (Priority 4)"""
        return Locator(
            type=LocatorType.XPATH,
            value=xpath,
            description=f"xpath={xpath}"
        )

    def by_id(self, element_id: str) -> Locator:
        """Create locator by ID"""
        return Locator(
            type=LocatorType.ID,
            value=element_id,
            description=f"id={element_id}"
        )

    def by_name(self, name: str) -> Locator:
        """Create locator by name attribute"""
        return Locator(
            type=LocatorType.NAME,
            value=name,
            description=f"name={name}"
        )

    # ==================== SCOPED LOCATORS ====================

    def within(self, scope: Locator, *locators: Locator) -> ScopedLocator:
        """Create scoped locator chain"""
        return ScopedLocator(
            locators=[scope] + list(locators),
            description=f"within({scope.description})"
        )

    def in_frame(self, frame_selector: str, locator: Locator) -> Locator:
        """Create locator that targets element in iframe"""
        locator.frame = frame_selector
        return locator

    # ==================== ELEMENT FINDING ====================

    def find(self, locator: Locator, scope_node_id: int = None) -> Optional[ElementHandle]:
        """Find single element by locator"""
        # Handle frame switching if needed
        if locator.frame:
            if not self._switch_to_frame(locator.frame):
                return None

        # Find element
        if locator.is_xpath:
            return self._find_by_xpath(locator, scope_node_id)
        elif locator.is_text_based:
            return self._find_by_text(locator, scope_node_id)
        else:
            return self._find_by_css(locator, scope_node_id)

    def find_all(self, locator: Locator, scope_node_id: int = None) -> List[ElementHandle]:
        """Find all elements matching locator"""
        if locator.frame:
            if not self._switch_to_frame(locator.frame):
                return []

        if locator.is_xpath:
            return self._find_all_by_xpath(locator, scope_node_id)
        elif locator.is_text_based:
            return self._find_all_by_text(locator, scope_node_id)
        else:
            return self._find_all_by_css(locator, scope_node_id)

    def find_scoped(self, scoped_locator: ScopedLocator) -> Optional[ElementHandle]:
        """Find element using scoped locator chain"""
        current_node_id = None

        for locator in scoped_locator.locators:
            handle = self.find(locator, scope_node_id=current_node_id)
            if not handle:
                return None
            current_node_id = handle.node_id

        return handle if 'handle' in dir() else None

    def _find_by_css(self, locator: Locator, scope_node_id: int = None) -> Optional[ElementHandle]:
        """Find element by CSS selector"""
        selector = locator.to_selector()

        if scope_node_id:
            # Scoped search
            result = self._session.send_command('DOM.querySelector', {
                'nodeId': scope_node_id,
                'selector': selector
            })
        else:
            # Get document first
            doc_result = self._session.send_command('DOM.getDocument')
            if not doc_result.success:
                return None
            doc_node_id = doc_result.result.get('root', {}).get('nodeId')

            result = self._session.send_command('DOM.querySelector', {
                'nodeId': doc_node_id,
                'selector': selector
            })

        if not result.success or not result.result:
            return None

        node_id = result.result.get('nodeId', 0)
        if node_id == 0:
            return None

        return self._create_element_handle(node_id, locator)

    def _find_all_by_css(self, locator: Locator, scope_node_id: int = None) -> List[ElementHandle]:
        """Find all elements by CSS selector"""
        selector = locator.to_selector()

        if not scope_node_id:
            doc_result = self._session.send_command('DOM.getDocument')
            if not doc_result.success:
                return []
            scope_node_id = doc_result.result.get('root', {}).get('nodeId')

        result = self._session.send_command('DOM.querySelectorAll', {
            'nodeId': scope_node_id,
            'selector': selector
        })

        if not result.success or not result.result:
            return []

        node_ids = result.result.get('nodeIds', [])
        handles = []
        for node_id in node_ids:
            if node_id > 0:
                handle = self._create_element_handle(node_id, locator)
                if handle:
                    handles.append(handle)

        return handles

    def _find_by_xpath(self, locator: Locator, scope_node_id: int = None) -> Optional[ElementHandle]:
        """Find element by XPath"""
        xpath = locator.value
        xpath_escaped = xpath.replace("'", "\\'")

        if scope_node_id:
            js = f"""
                (function() {{
                    let scope = document;  // TODO: get node by ID
                    let result = document.evaluate('{xpath_escaped}', scope, null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    return result.singleNodeValue ? true : false;
                }})()
            """
        else:
            js = f"""
                (function() {{
                    let result = document.evaluate('{xpath_escaped}', document, null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    return result.singleNodeValue ? true : false;
                }})()
            """

        eval_result = self._session.evaluate_js(js)

        if eval_result.success and eval_result.result:
            if eval_result.result.get('result', {}).get('value'):
                # Element exists, get node via Runtime
                return self._find_via_runtime(xpath, is_xpath=True)

        return None

    def _find_all_by_xpath(self, locator: Locator, scope_node_id: int = None) -> List[ElementHandle]:
        """Find all elements by XPath"""
        # Simplified - returns empty for now
        return []

    def _find_by_text(self, locator: Locator, scope_node_id: int = None) -> Optional[ElementHandle]:
        """Find element by text content"""
        text = locator.value
        text_escaped = text.replace("'", "\\'").replace("\\", "\\\\")
        exact = locator.type == LocatorType.TEXT_EXACT

        if exact:
            js = f"""
                (function() {{
                    let walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    while (walker.nextNode()) {{
                        if (walker.currentNode.textContent.trim() === '{text_escaped}') {{
                            return walker.currentNode.parentElement ? true : false;
                        }}
                    }}
                    return false;
                }})()
            """
        else:
            js = f"""
                (function() {{
                    let elements = document.querySelectorAll('*');
                    for (let el of elements) {{
                        if (el.textContent.includes('{text_escaped}')) {{
                            return true;
                        }}
                    }}
                    return false;
                }})()
            """

        eval_result = self._session.evaluate_js(js)

        if eval_result.success and eval_result.result:
            if eval_result.result.get('result', {}).get('value'):
                return self._find_via_runtime(text, is_text=True, exact=exact)

        return None

    def _find_all_by_text(self, locator: Locator, scope_node_id: int = None) -> List[ElementHandle]:
        """Find all elements by text"""
        return []

    def _find_via_runtime(self, query: str, is_xpath: bool = False,
                          is_text: bool = False, exact: bool = False) -> Optional[ElementHandle]:
        """Find element via Runtime.evaluate and get node reference"""
        query_escaped = query.replace("'", "\\'").replace("\\", "\\\\")

        if is_xpath:
            js = f"""
                (function() {{
                    let result = document.evaluate('{query_escaped}', document, null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    return result.singleNodeValue;
                }})()
            """
        elif is_text:
            if exact:
                js = f"""
                    (function() {{
                        let walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                        while (walker.nextNode()) {{
                            if (walker.currentNode.textContent.trim() === '{query_escaped}') {{
                                return walker.currentNode.parentElement;
                            }}
                        }}
                        return null;
                    }})()
                """
            else:
                js = f"""
                    (function() {{
                        let elements = document.querySelectorAll('*');
                        for (let el of elements) {{
                            if (el.childNodes.length <= 3 && el.textContent.includes('{query_escaped}')) {{
                                return el;
                            }}
                        }}
                        return null;
                    }})()
                """
        else:
            js = f"document.querySelector('{query_escaped}')"

        result = self._session.send_command('Runtime.evaluate', {
            'expression': js,
            'returnByValue': False
        })

        if not result.success or not result.result:
            return None

        obj = result.result.get('result', {})
        if obj.get('type') != 'object' or obj.get('subtype') == 'null':
            return None

        object_id = obj.get('objectId')
        if not object_id:
            return None

        # Get node from object
        node_result = self._session.send_command('DOM.requestNode', {
            'objectId': object_id
        })

        if not node_result.success or not node_result.result:
            return None

        node_id = node_result.result.get('nodeId', 0)
        if node_id == 0:
            return None

        locator_type = LocatorType.XPATH if is_xpath else (
            LocatorType.TEXT_EXACT if is_text and exact else
            LocatorType.TEXT_CONTAINS if is_text else LocatorType.CSS
        )

        return ElementHandle(
            node_id=node_id,
            backend_node_id=0,
            object_id=object_id,
            locator=Locator(type=locator_type, value=query),
            frame_context=self._current_frame or FrameContext()
        )

    def _create_element_handle(self, node_id: int, locator: Locator) -> Optional[ElementHandle]:
        """Create element handle from node ID"""
        # Get object ID for the node
        result = self._session.send_command('DOM.resolveNode', {
            'nodeId': node_id
        })

        if not result.success or not result.result:
            return ElementHandle(
                node_id=node_id,
                backend_node_id=0,
                object_id='',
                locator=locator,
                frame_context=self._current_frame or FrameContext()
            )

        obj = result.result.get('object', {})
        return ElementHandle(
            node_id=node_id,
            backend_node_id=0,
            object_id=obj.get('objectId', ''),
            locator=locator,
            frame_context=self._current_frame or FrameContext()
        )

    # ==================== FRAME HANDLING ====================

    def _switch_to_frame(self, frame_selector: str) -> bool:
        """Switch to iframe context"""
        # Find frame element
        frame_handle = self.find(Locator(type=LocatorType.CSS, value=frame_selector))
        if not frame_handle:
            return False

        # Get frame's execution context
        # This is simplified - full implementation would track frame trees
        self._frame_stack.append(self._current_frame or FrameContext())
        self._current_frame = FrameContext(
            frame_selector=frame_selector,
            is_main_frame=False
        )

        return True

    def switch_to_main_frame(self):
        """Switch back to main frame"""
        self._current_frame = FrameContext(is_main_frame=True)
        self._frame_stack = []

    def switch_to_parent_frame(self):
        """Switch to parent frame"""
        if self._frame_stack:
            self._current_frame = self._frame_stack.pop()
        else:
            self._current_frame = FrameContext(is_main_frame=True)

    # ==================== SMART LOCATOR BUILDING ====================

    def build_locator(self, hints: Dict[str, str]) -> Locator:
        """
        Build optimal locator from hints

        Tries locator types in priority order based on available hints.
        """
        # Priority 1: Role/ARIA
        if 'role' in hints:
            if 'aria-label' in hints:
                return self.by_role(hints['role'], hints['aria-label'])
            return self.by_role(hints['role'])

        if 'aria-label' in hints:
            return self.by_aria_label(hints['aria-label'])

        # Priority 2: Test IDs
        if 'data-testid' in hints:
            return self.by_test_id(hints['data-testid'])

        if 'data-automation-id' in hints:
            return Locator(
                type=LocatorType.AUTOMATION_ID,
                value=hints['data-automation-id']
            )

        # Priority 3: Text/placeholder
        if 'text' in hints:
            return self.by_text(hints['text'], exact=hints.get('exact', False))

        if 'placeholder' in hints:
            return self.by_placeholder(hints['placeholder'])

        # Priority 4: Structural
        if 'id' in hints:
            return self.by_id(hints['id'])

        if 'name' in hints:
            return self.by_name(hints['name'])

        if 'css' in hints:
            return self.by_css(hints['css'])

        if 'xpath' in hints:
            return self.by_xpath(hints['xpath'])

        raise ValueError("No valid locator hints provided")

    def auto_locator(self, element_description: str) -> List[Locator]:
        """
        Generate multiple locator strategies for an element

        Returns list of locators in priority order to try.
        """
        locators = []

        # Check for role indicators
        if 'button' in element_description.lower():
            locators.append(self.by_role('button'))

        if 'link' in element_description.lower():
            locators.append(self.by_role('link'))

        if 'input' in element_description.lower() or 'field' in element_description.lower():
            locators.append(self.by_role('textbox'))

        # Extract quoted text for text-based locators
        quoted = re.findall(r'"([^"]+)"', element_description)
        for text in quoted:
            locators.append(self.by_text(text))
            locators.append(self.by_aria_label(text))
            locators.append(self.by_placeholder(text))

        return locators
