"""
Connection Layer MAX - CDP Session Management

Features:
- Attach lifecycle: connect → create session → subscribe events → graceful close
- Auto-reconnect with state rehydration
- Heartbeat/health check
- Backpressure: limit in-flight commands
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import threading
import queue
import json
import time
import websocket
import requests

from .events import EventEmitter, CDPEvent, EventType
from .observability import ReasonCode, FailureReason, get_observability


class SessionState(Enum):
    """Session lifecycle states"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    SUBSCRIBING = auto()
    READY = auto()
    RECONNECTING = auto()
    RECOVERING = auto()
    CLOSING = auto()
    CLOSED = auto()
    FAILED = auto()


@dataclass
class SessionConfig:
    """Session configuration"""
    # Connection
    remote_port: int = 0
    ws_url: Optional[str] = None  # Direct WebSocket URL (from browser API)
    connect_timeout_ms: int = 30000
    max_connect_retries: int = 3
    connect_retry_delay_ms: int = 1000

    # Reconnection
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5
    reconnect_delay_ms: int = 2000
    reconnect_backoff_multiplier: float = 1.5
    max_reconnect_delay_ms: int = 30000

    # Heartbeat
    heartbeat_interval_ms: int = 5000
    heartbeat_timeout_ms: int = 10000
    max_heartbeat_failures: int = 3

    # Backpressure
    max_in_flight_commands: int = 20
    command_timeout_ms: int = 30000
    command_queue_size: int = 100

    # Events to subscribe
    subscribed_domains: List[str] = field(default_factory=lambda: [
        'Page', 'Network', 'Runtime', 'Target', 'DOM'
    ])


@dataclass
class CommandResult:
    """Result from a CDP command"""
    success: bool
    result: Optional[Dict] = None
    error: Optional[str] = None
    error_code: Optional[int] = None
    duration_ms: int = 0


class CDPSession:
    """
    CDP Session with MAX features

    Lifecycle: DISCONNECTED → CONNECTING → CONNECTED → SUBSCRIBING → READY
    Recovery: READY → RECONNECTING → RECOVERING → READY
    """

    def __init__(self, config: SessionConfig):
        self.config = config
        self.state = SessionState.DISCONNECTED
        self.events = EventEmitter()

        # WebSocket
        self._ws: Optional[websocket.WebSocket] = None
        self._ws_url: Optional[str] = None
        self._target_id: Optional[str] = None

        # Command tracking
        self._msg_id = 0
        self._pending_commands: Dict[int, queue.Queue] = {}
        self._command_semaphore = threading.Semaphore(config.max_in_flight_commands)
        self._lock = threading.Lock()

        # Heartbeat
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_failures = 0
        self._last_heartbeat = datetime.now()
        self._stop_heartbeat = threading.Event()

        # Receiver thread
        self._receiver_thread: Optional[threading.Thread] = None
        self._stop_receiver = threading.Event()

        # State for recovery
        self._subscribed_domains: List[str] = []
        self._reconnect_attempts = 0

        # Observability
        self._obs = get_observability()

    @property
    def is_connected(self) -> bool:
        return self.state in [SessionState.CONNECTED, SessionState.SUBSCRIBING,
                              SessionState.READY, SessionState.RECOVERING]

    @property
    def is_ready(self) -> bool:
        return self.state == SessionState.READY

    def connect(self, ws_url: str = None) -> Tuple[bool, Optional[FailureReason]]:
        """
        Connect to browser via CDP

        Args:
            ws_url: Optional WebSocket URL (overrides config.ws_url)

        Returns: (success, failure_reason)
        """
        if self.is_connected:
            return True, None

        self.state = SessionState.CONNECTING
        self.events.emit(CDPEvent(type=EventType.CDP_RECONNECTING, data={'state': 'connecting'}))

        # Use provided ws_url or config ws_url
        direct_ws_url = ws_url or self.config.ws_url

        for attempt in range(self.config.max_connect_retries):
            try:
                if direct_ws_url:
                    # Use direct WebSocket URL (bypasses /json endpoint and origin issues)
                    self._ws_url = direct_ws_url
                    self._target_id = None
                else:
                    # Fallback: Get page list from /json endpoint
                    base_url = f"http://127.0.0.1:{self.config.remote_port}"
                    resp = requests.get(f"{base_url}/json", timeout=10)
                    pages = resp.json()

                    # Find main page
                    page = None
                    for p in pages:
                        url = p.get('url', '')
                        ptype = p.get('type', '')
                        if ptype == 'page' and not url.startswith('devtools://'):
                            page = p
                            break

                    if not page and pages:
                        page = pages[0]

                    if not page:
                        raise Exception("No page found in browser")

                    self._ws_url = page.get('webSocketDebuggerUrl', '')
                    self._target_id = page.get('id')

                    if not self._ws_url:
                        raise Exception("No WebSocket URL in page info")

                # Connect WebSocket (suppress origin header to bypass Chrome check)
                if direct_ws_url:
                    # Use suppress_origin=True to completely skip origin header
                    self._ws = websocket.create_connection(
                        self._ws_url,
                        timeout=self.config.connect_timeout_ms / 1000,
                        suppress_origin=True
                    )
                else:
                    # Try with suppress_origin first, then fallback to with origin
                    try:
                        self._ws = websocket.create_connection(
                            self._ws_url,
                            timeout=self.config.connect_timeout_ms / 1000,
                            suppress_origin=True
                        )
                    except Exception:
                        self._ws = websocket.create_connection(
                            self._ws_url,
                            timeout=self.config.connect_timeout_ms / 1000,
                            origin=f"http://127.0.0.1:{self.config.remote_port}"
                        )

                self.state = SessionState.CONNECTED

                # Start receiver thread
                self._start_receiver()

                # Subscribe to domains
                self._subscribe_domains()

                # Start heartbeat
                self._start_heartbeat()

                self.state = SessionState.READY
                self._reconnect_attempts = 0

                self.events.emit(CDPEvent(type=EventType.CDP_CONNECTED, data={
                    'ws_url': self._ws_url,
                    'target_id': self._target_id
                }))

                return True, None

            except Exception as e:
                if attempt < self.config.max_connect_retries - 1:
                    time.sleep(self.config.connect_retry_delay_ms / 1000)
                else:
                    self.state = SessionState.FAILED
                    reason = FailureReason(
                        code=ReasonCode.CDP_DISCONNECTED,
                        message=f"Connect failed after {attempt + 1} attempts: {str(e)}",
                        recoverable=True
                    )
                    return False, reason

        return False, FailureReason(
            code=ReasonCode.CDP_DISCONNECTED,
            message="Max connect retries exceeded",
            recoverable=True
        )

    def _subscribe_domains(self):
        """Subscribe to CDP domains"""
        self.state = SessionState.SUBSCRIBING
        self._subscribed_domains = []

        for domain in self.config.subscribed_domains:
            try:
                result = self.send_command(f'{domain}.enable', timeout_ms=5000)
                if result.success:
                    self._subscribed_domains.append(domain)
            except Exception:
                pass  # Some domains may not be available

    def _start_receiver(self):
        """Start WebSocket receiver thread"""
        self._stop_receiver.clear()
        self._receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self._receiver_thread.start()

    def _receiver_loop(self):
        """Receive and dispatch CDP messages"""
        while not self._stop_receiver.is_set():
            try:
                if self._ws is None:
                    break

                self._ws.settimeout(0.5)
                try:
                    data = self._ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue

                if not data:
                    continue

                msg = json.loads(data)

                # Handle command response
                if 'id' in msg:
                    msg_id = msg['id']
                    with self._lock:
                        if msg_id in self._pending_commands:
                            self._pending_commands[msg_id].put(msg)

                # Handle event
                elif 'method' in msg:
                    method = msg['method']
                    params = msg.get('params', {})
                    event = CDPEvent.from_cdp_message(method, params, target_id=self._target_id)
                    if event:
                        self.events.emit(event)

                    # Check for disconnect events
                    if method == 'Inspector.detached':
                        self._handle_disconnect('Inspector detached')

            except websocket.WebSocketConnectionClosedException:
                self._handle_disconnect('WebSocket closed')
                break
            except Exception as e:
                if not self._stop_receiver.is_set():
                    self._handle_disconnect(f'Receiver error: {str(e)}')
                break

    def _start_heartbeat(self):
        """Start heartbeat thread"""
        self._stop_heartbeat.clear()
        self._heartbeat_failures = 0
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        """Periodic heartbeat to check connection health"""
        while not self._stop_heartbeat.is_set():
            time.sleep(self.config.heartbeat_interval_ms / 1000)

            if self._stop_heartbeat.is_set():
                break

            if not self.is_connected:
                continue

            try:
                # Simple health check - evaluate JS
                result = self.send_command('Runtime.evaluate', {
                    'expression': 'true',
                    'returnByValue': True
                }, timeout_ms=self.config.heartbeat_timeout_ms)

                if result.success:
                    self._heartbeat_failures = 0
                    self._last_heartbeat = datetime.now()
                else:
                    self._heartbeat_failures += 1
                    if self._heartbeat_failures >= self.config.max_heartbeat_failures:
                        self.events.emit(CDPEvent(type=EventType.HEARTBEAT_FAILED, data={
                            'failures': self._heartbeat_failures
                        }))
                        self._handle_disconnect('Heartbeat failed')

            except Exception as e:
                self._heartbeat_failures += 1
                if self._heartbeat_failures >= self.config.max_heartbeat_failures:
                    self._handle_disconnect(f'Heartbeat exception: {str(e)}')

    def _handle_disconnect(self, reason: str):
        """Handle unexpected disconnection"""
        if self.state in [SessionState.CLOSING, SessionState.CLOSED, SessionState.RECONNECTING]:
            return

        self.events.emit(CDPEvent(type=EventType.CDP_DISCONNECTED, data={'reason': reason}))

        if self.config.auto_reconnect:
            self._attempt_reconnect()
        else:
            self.state = SessionState.DISCONNECTED

    def _attempt_reconnect(self):
        """Attempt to reconnect with backoff"""
        if self.state == SessionState.RECONNECTING:
            return

        self.state = SessionState.RECONNECTING
        self.events.emit(CDPEvent(type=EventType.CDP_RECONNECTING, data={'attempt': self._reconnect_attempts}))

        # Stop current threads
        self._stop_receiver.set()
        self._stop_heartbeat.set()

        # Close existing connection
        if self._ws:
            try:
                self._ws.close()
            except:
                pass
            self._ws = None

        # Backoff delay
        delay = min(
            self.config.reconnect_delay_ms * (self.config.reconnect_backoff_multiplier ** self._reconnect_attempts),
            self.config.max_reconnect_delay_ms
        )

        while self._reconnect_attempts < self.config.max_reconnect_attempts:
            self._reconnect_attempts += 1

            time.sleep(delay / 1000)

            success, reason = self.connect()
            if success:
                self.state = SessionState.RECOVERING
                self._rehydrate_state()
                self.state = SessionState.READY
                return

            delay = min(delay * self.config.reconnect_backoff_multiplier, self.config.max_reconnect_delay_ms)

        # Reconnection failed
        self.state = SessionState.FAILED
        self.events.emit(CDPEvent(type=EventType.CDP_ERROR, data={
            'error': 'Max reconnect attempts exceeded'
        }))

    def _rehydrate_state(self):
        """Re-subscribe to domains after reconnect"""
        for domain in self._subscribed_domains:
            try:
                self.send_command(f'{domain}.enable', timeout_ms=5000)
            except:
                pass

    def send_command(self, method: str, params: Dict = None,
                     timeout_ms: int = None) -> CommandResult:
        """
        Send a CDP command with backpressure control

        Features:
        - Semaphore limits concurrent commands
        - Timeout handling
        - Response matching by ID
        """
        if not self.is_connected:
            return CommandResult(
                success=False,
                error="Not connected"
            )

        timeout = timeout_ms or self.config.command_timeout_ms

        # Backpressure - wait for slot
        if not self._command_semaphore.acquire(timeout=timeout / 1000):
            return CommandResult(
                success=False,
                error="Command queue full (backpressure)"
            )

        start_time = datetime.now()
        response_queue: queue.Queue = queue.Queue()

        try:
            with self._lock:
                self._msg_id += 1
                msg_id = self._msg_id
                self._pending_commands[msg_id] = response_queue

            # Send command
            msg = {
                'id': msg_id,
                'method': method,
                'params': params or {}
            }

            self._ws.send(json.dumps(msg))

            # Wait for response
            try:
                response = response_queue.get(timeout=timeout / 1000)
            except queue.Empty:
                return CommandResult(
                    success=False,
                    error=f"Timeout waiting for {method}",
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                )

            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            if 'error' in response:
                return CommandResult(
                    success=False,
                    error=response['error'].get('message', 'Unknown error'),
                    error_code=response['error'].get('code'),
                    duration_ms=duration
                )

            return CommandResult(
                success=True,
                result=response.get('result'),
                duration_ms=duration
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e),
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )

        finally:
            with self._lock:
                self._pending_commands.pop(msg_id, None)
            self._command_semaphore.release()

    def evaluate_js(self, expression: str, await_promise: bool = True,
                    timeout_ms: int = None) -> CommandResult:
        """Evaluate JavaScript expression"""
        return self.send_command('Runtime.evaluate', {
            'expression': expression,
            'returnByValue': True,
            'awaitPromise': await_promise
        }, timeout_ms=timeout_ms)

    def get_current_url(self) -> Optional[str]:
        """Get current page URL"""
        result = self.evaluate_js('window.location.href', await_promise=False)
        if result.success and result.result:
            return result.result.get('result', {}).get('value')
        return None

    def get_document(self) -> Optional[Dict]:
        """Get document node"""
        result = self.send_command('DOM.getDocument')
        if result.success and result.result:
            return result.result.get('root')
        return None

    def close(self):
        """Gracefully close session"""
        self.state = SessionState.CLOSING

        # Stop threads
        self._stop_heartbeat.set()
        self._stop_receiver.set()

        # Disable domains
        for domain in self._subscribed_domains:
            try:
                self.send_command(f'{domain}.disable', timeout_ms=1000)
            except:
                pass

        # Close WebSocket
        if self._ws:
            try:
                self._ws.close()
            except:
                pass
            self._ws = None

        self.state = SessionState.CLOSED

    def get_health_status(self) -> Dict:
        """Get session health status"""
        return {
            'state': self.state.name,
            'is_connected': self.is_connected,
            'is_ready': self.is_ready,
            'heartbeat_failures': self._heartbeat_failures,
            'last_heartbeat': self._last_heartbeat.isoformat(),
            'reconnect_attempts': self._reconnect_attempts,
            'pending_commands': len(self._pending_commands),
            'subscribed_domains': self._subscribed_domains
        }
