"""
Event-driven MAX - CDP event subscription and event-based synchronization

No polling where events can be used instead.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
import threading
import queue
import json


class EventType(Enum):
    """CDP event types we care about"""
    # Page lifecycle
    PAGE_LOAD_EVENT_FIRED = "Page.loadEventFired"
    PAGE_DOM_CONTENT_LOADED = "Page.domContentEventFired"
    PAGE_FRAME_NAVIGATED = "Page.frameNavigated"
    PAGE_FRAME_STOPPED_LOADING = "Page.frameStoppedLoading"
    PAGE_LIFECYCLE_EVENT = "Page.lifecycleEvent"
    PAGE_JAVASCRIPT_DIALOG = "Page.javascriptDialogOpening"

    # Network events
    NETWORK_REQUEST_WILL_BE_SENT = "Network.requestWillBeSent"
    NETWORK_RESPONSE_RECEIVED = "Network.responseReceived"
    NETWORK_LOADING_FINISHED = "Network.loadingFinished"
    NETWORK_LOADING_FAILED = "Network.loadingFailed"
    NETWORK_REQUEST_SERVED_FROM_CACHE = "Network.requestServedFromCache"

    # Target events
    TARGET_CREATED = "Target.targetCreated"
    TARGET_DESTROYED = "Target.targetDestroyed"
    TARGET_INFO_CHANGED = "Target.targetInfoChanged"
    TARGET_CRASHED = "Target.targetCrashed"
    TARGET_ATTACHED = "Target.attachedToTarget"
    TARGET_DETACHED = "Target.detachedFromTarget"

    # Runtime events
    RUNTIME_CONSOLE_API_CALLED = "Runtime.consoleAPICalled"
    RUNTIME_EXCEPTION_THROWN = "Runtime.exceptionThrown"
    RUNTIME_EXECUTION_CONTEXT_CREATED = "Runtime.executionContextCreated"
    RUNTIME_EXECUTION_CONTEXT_DESTROYED = "Runtime.executionContextDestroyed"

    # DOM events
    DOM_DOCUMENT_UPDATED = "DOM.documentUpdated"
    DOM_CHILD_NODE_INSERTED = "DOM.childNodeInserted"
    DOM_CHILD_NODE_REMOVED = "DOM.childNodeRemoved"
    DOM_ATTRIBUTE_MODIFIED = "DOM.attributeModified"

    # Download events
    BROWSER_DOWNLOAD_WILL_BEGIN = "Browser.downloadWillBegin"
    BROWSER_DOWNLOAD_PROGRESS = "Browser.downloadProgress"

    # File chooser
    PAGE_FILE_CHOOSER_OPENED = "Page.fileChooserOpened"

    # Inspector
    INSPECTOR_DETACHED = "Inspector.detached"

    # Custom internal events
    CDP_CONNECTED = "cdp.connected"
    CDP_DISCONNECTED = "cdp.disconnected"
    CDP_RECONNECTING = "cdp.reconnecting"
    CDP_ERROR = "cdp.error"
    HEARTBEAT_FAILED = "cdp.heartbeatFailed"


@dataclass
class CDPEvent:
    """A CDP event with metadata"""
    type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    target_id: Optional[str] = None

    @classmethod
    def from_cdp_message(cls, method: str, params: Dict, session_id: str = None,
                          target_id: str = None) -> Optional['CDPEvent']:
        """Create event from CDP message"""
        try:
            event_type = EventType(method)
            return cls(
                type=event_type,
                data=params,
                session_id=session_id,
                target_id=target_id
            )
        except ValueError:
            # Unknown event type
            return None


EventCallback = Callable[[CDPEvent], None]


class EventEmitter:
    """
    Event emitter for CDP events

    Features:
    - Subscribe to specific event types
    - Pattern matching for event data
    - Async event waiting
    - Event history
    """

    def __init__(self, history_size: int = 1000):
        self._listeners: Dict[EventType, List[EventCallback]] = {}
        self._once_listeners: Dict[EventType, List[EventCallback]] = {}
        self._waiters: Dict[str, queue.Queue] = {}
        self._history: List[CDPEvent] = []
        self._history_size = history_size
        self._lock = threading.Lock()
        self._paused = False

    def on(self, event_type: EventType, callback: EventCallback) -> Callable:
        """Subscribe to an event type"""
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)

        def unsubscribe():
            with self._lock:
                if event_type in self._listeners:
                    self._listeners[event_type].remove(callback)

        return unsubscribe

    def once(self, event_type: EventType, callback: EventCallback):
        """Subscribe to an event type once"""
        with self._lock:
            if event_type not in self._once_listeners:
                self._once_listeners[event_type] = []
            self._once_listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: EventCallback = None):
        """Unsubscribe from an event type"""
        with self._lock:
            if callback is None:
                self._listeners.pop(event_type, None)
                self._once_listeners.pop(event_type, None)
            else:
                if event_type in self._listeners:
                    self._listeners[event_type] = [
                        cb for cb in self._listeners[event_type] if cb != callback
                    ]
                if event_type in self._once_listeners:
                    self._once_listeners[event_type] = [
                        cb for cb in self._once_listeners[event_type] if cb != callback
                    ]

    def emit(self, event: CDPEvent):
        """Emit an event to all listeners"""
        if self._paused:
            return

        # Add to history
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._history_size:
                self._history = self._history[-self._history_size:]

        # Regular listeners
        listeners = []
        with self._lock:
            if event.type in self._listeners:
                listeners = self._listeners[event.type].copy()

        for callback in listeners:
            try:
                callback(event)
            except Exception:
                pass  # Don't let listener errors break event flow

        # Once listeners
        once_listeners = []
        with self._lock:
            if event.type in self._once_listeners:
                once_listeners = self._once_listeners[event.type].copy()
                self._once_listeners[event.type] = []

        for callback in once_listeners:
            try:
                callback(event)
            except Exception:
                pass

        # Notify waiters
        with self._lock:
            for waiter_id, q in list(self._waiters.items()):
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass

    def wait_for(self, event_type: EventType, timeout_ms: int = 30000,
                 condition: Callable[[CDPEvent], bool] = None) -> Optional[CDPEvent]:
        """
        Wait for a specific event type

        Args:
            event_type: The event type to wait for
            timeout_ms: Maximum wait time
            condition: Optional filter function for the event data

        Returns:
            The matching event or None on timeout
        """
        waiter_id = f"{event_type.value}_{datetime.now().timestamp()}"
        q: queue.Queue = queue.Queue(maxsize=100)

        with self._lock:
            self._waiters[waiter_id] = q

        try:
            deadline = datetime.now().timestamp() + (timeout_ms / 1000)
            while datetime.now().timestamp() < deadline:
                remaining = deadline - datetime.now().timestamp()
                if remaining <= 0:
                    break
                try:
                    event = q.get(timeout=min(remaining, 0.1))
                    if event.type == event_type:
                        if condition is None or condition(event):
                            return event
                except queue.Empty:
                    continue
            return None
        finally:
            with self._lock:
                self._waiters.pop(waiter_id, None)

    def wait_for_any(self, event_types: List[EventType], timeout_ms: int = 30000) -> Optional[CDPEvent]:
        """Wait for any of the specified event types"""
        waiter_id = f"any_{datetime.now().timestamp()}"
        q: queue.Queue = queue.Queue(maxsize=100)

        with self._lock:
            self._waiters[waiter_id] = q

        try:
            deadline = datetime.now().timestamp() + (timeout_ms / 1000)
            while datetime.now().timestamp() < deadline:
                remaining = deadline - datetime.now().timestamp()
                if remaining <= 0:
                    break
                try:
                    event = q.get(timeout=min(remaining, 0.1))
                    if event.type in event_types:
                        return event
                except queue.Empty:
                    continue
            return None
        finally:
            with self._lock:
                self._waiters.pop(waiter_id, None)

    def wait_for_network(self, url_pattern: str = None, timeout_ms: int = 30000) -> Optional[CDPEvent]:
        """Wait for a network response matching pattern"""
        def condition(event: CDPEvent) -> bool:
            if url_pattern is None:
                return True
            url = event.data.get('response', {}).get('url', '')
            if not url:
                url = event.data.get('request', {}).get('url', '')
            return url_pattern in url

        return self.wait_for(EventType.NETWORK_RESPONSE_RECEIVED, timeout_ms, condition)

    def wait_for_navigation(self, timeout_ms: int = 30000) -> Optional[CDPEvent]:
        """Wait for navigation to complete"""
        return self.wait_for(EventType.PAGE_LOAD_EVENT_FIRED, timeout_ms)

    def get_history(self, event_type: EventType = None, limit: int = 100) -> List[CDPEvent]:
        """Get recent events from history"""
        with self._lock:
            if event_type:
                filtered = [e for e in self._history if e.type == event_type]
            else:
                filtered = self._history.copy()
            return filtered[-limit:]

    def get_pending_requests(self) -> Set[str]:
        """Get IDs of pending network requests"""
        pending = set()
        with self._lock:
            for event in self._history:
                if event.type == EventType.NETWORK_REQUEST_WILL_BE_SENT:
                    request_id = event.data.get('requestId')
                    if request_id:
                        pending.add(request_id)
                elif event.type in [EventType.NETWORK_LOADING_FINISHED,
                                    EventType.NETWORK_LOADING_FAILED]:
                    request_id = event.data.get('requestId')
                    pending.discard(request_id)
        return pending

    def clear_history(self):
        """Clear event history"""
        with self._lock:
            self._history = []

    def pause(self):
        """Pause event emission"""
        self._paused = True

    def resume(self):
        """Resume event emission"""
        self._paused = False


class NetworkMonitor:
    """
    Monitor network activity for idle detection

    Tracks pending requests and determines when network is idle.
    """

    def __init__(self, emitter: EventEmitter, idle_threshold_ms: int = 500):
        self._emitter = emitter
        self._idle_threshold_ms = idle_threshold_ms
        self._pending_requests: Dict[str, datetime] = {}
        self._last_activity = datetime.now()
        self._lock = threading.Lock()

        # Subscribe to network events
        emitter.on(EventType.NETWORK_REQUEST_WILL_BE_SENT, self._on_request_sent)
        emitter.on(EventType.NETWORK_LOADING_FINISHED, self._on_request_complete)
        emitter.on(EventType.NETWORK_LOADING_FAILED, self._on_request_complete)

    def _on_request_sent(self, event: CDPEvent):
        request_id = event.data.get('requestId')
        if request_id:
            with self._lock:
                self._pending_requests[request_id] = datetime.now()
                self._last_activity = datetime.now()

    def _on_request_complete(self, event: CDPEvent):
        request_id = event.data.get('requestId')
        if request_id:
            with self._lock:
                self._pending_requests.pop(request_id, None)
                self._last_activity = datetime.now()

    def is_idle(self) -> bool:
        """Check if network is idle (no pending requests)"""
        with self._lock:
            if self._pending_requests:
                return False
            elapsed = (datetime.now() - self._last_activity).total_seconds() * 1000
            return elapsed >= self._idle_threshold_ms

    def get_pending_count(self) -> int:
        """Get number of pending requests"""
        with self._lock:
            return len(self._pending_requests)

    def wait_for_idle(self, timeout_ms: int = 30000) -> bool:
        """Wait for network to become idle"""
        deadline = datetime.now().timestamp() + (timeout_ms / 1000)
        while datetime.now().timestamp() < deadline:
            if self.is_idle():
                return True
            import time
            time.sleep(0.1)
        return False
