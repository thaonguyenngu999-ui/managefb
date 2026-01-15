"""
CDP Stealth Module - Anti-detection & stability features

Features:
1. Runtime domain minimization & side-effect mitigation
2. CDP command pattern obfuscation & rate limiting
3. WebRTC & media device leak prevention
4. Service Worker & Fetch interception hardening
5. Memory & DOM leak monitoring
6. Isolated world consistency & world pinning

Target: Pass browserscan.net and similar anti-bot detection
"""

import random
import time
import threading
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import deque


# ==================== 1. RUNTIME DOMAIN MINIMIZATION ====================

class DomainState(Enum):
    """State of a CDP domain"""
    DISABLED = auto()
    ENABLED = auto()
    SUSPENDED = auto()  # Temporarily disabled


@dataclass
class DomainUsage:
    """Track domain usage for lazy enable/disable"""
    domain: str
    state: DomainState = DomainState.DISABLED
    last_used: Optional[datetime] = None
    use_count: int = 0
    auto_disable_after_ms: int = 5000  # Auto-disable after 5s of inactivity


class RuntimeDomainManager:
    """
    Manages CDP domains with minimal footprint

    Key principle: Only enable domains when needed, disable immediately after
    This reduces anti-bot detection via Runtime signals
    """

    def __init__(self, session):
        self._session = session
        self._domains: Dict[str, DomainUsage] = {}
        self._lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()

        # Domains that should stay enabled (minimal set)
        self._persistent_domains: Set[str] = {'Page'}  # Only Page is essential

        # Domains that are high-risk for detection
        self._high_risk_domains: Set[str] = {
            'Runtime',  # Most detected - leaks CDP presence
            'DOM',      # Can be detected via side effects
            'Debugger', # Obviously suspicious
            'Profiler', # Obviously suspicious
        }

        # Domain dependencies
        self._domain_deps: Dict[str, List[str]] = {
            'Runtime': [],
            'DOM': [],
            'Network': [],
            'Page': [],
            'Input': [],
            'Emulation': [],
        }

    def start_cleanup_thread(self):
        """Start background thread to auto-disable unused domains"""
        self._stop_cleanup.clear()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def stop_cleanup_thread(self):
        """Stop cleanup thread"""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)

    def _cleanup_loop(self):
        """Periodically disable unused domains"""
        while not self._stop_cleanup.is_set():
            time.sleep(1)  # Check every second

            if self._stop_cleanup.is_set():
                break

            self._auto_disable_unused()

    def _auto_disable_unused(self):
        """Disable domains that haven't been used recently"""
        now = datetime.now()

        with self._lock:
            for domain, usage in list(self._domains.items()):
                # Skip persistent domains
                if domain in self._persistent_domains:
                    continue

                # Skip already disabled
                if usage.state != DomainState.ENABLED:
                    continue

                # Check if unused for too long
                if usage.last_used:
                    elapsed = (now - usage.last_used).total_seconds() * 1000
                    if elapsed > usage.auto_disable_after_ms:
                        self._disable_domain_internal(domain)

    def require_domain(self, domain: str) -> bool:
        """
        Ensure domain is enabled before use

        Usage:
            with domain_manager.require_domain('Runtime'):
                session.send_command('Runtime.evaluate', ...)
        """
        with self._lock:
            if domain not in self._domains:
                self._domains[domain] = DomainUsage(domain=domain)

            usage = self._domains[domain]

            if usage.state == DomainState.ENABLED:
                usage.last_used = datetime.now()
                usage.use_count += 1
                return True

            # Enable domain
            return self._enable_domain_internal(domain)

    def _enable_domain_internal(self, domain: str) -> bool:
        """Enable a domain (internal, lock already held)"""
        # Check dependencies first
        for dep in self._domain_deps.get(domain, []):
            if dep not in self._domains or self._domains[dep].state != DomainState.ENABLED:
                self._enable_domain_internal(dep)

        try:
            result = self._session.send_command(f'{domain}.enable', timeout_ms=5000)
            if result.success:
                self._domains[domain].state = DomainState.ENABLED
                self._domains[domain].last_used = datetime.now()
                return True
        except Exception:
            pass

        return False

    def _disable_domain_internal(self, domain: str) -> bool:
        """Disable a domain (internal, lock already held)"""
        if domain in self._persistent_domains:
            return False

        try:
            result = self._session.send_command(f'{domain}.disable', timeout_ms=2000)
            if result.success:
                self._domains[domain].state = DomainState.DISABLED
                return True
        except Exception:
            pass

        return False

    def release_domain(self, domain: str):
        """
        Mark domain as no longer needed
        High-risk domains are disabled immediately
        """
        with self._lock:
            if domain not in self._domains:
                return

            # High-risk domains: disable immediately
            if domain in self._high_risk_domains:
                self._disable_domain_internal(domain)
            else:
                # Others: update last_used, let cleanup handle it
                self._domains[domain].last_used = datetime.now()

    def evaluate_minimal(self, expression: str, timeout_ms: int = 5000) -> Any:
        """
        Evaluate JS with minimal Runtime domain exposure
        Enable -> Evaluate -> Disable (for high-risk)
        """
        self.require_domain('Runtime')

        try:
            result = self._session.send_command('Runtime.evaluate', {
                'expression': expression,
                'returnByValue': True,
                'awaitPromise': False
            }, timeout_ms=timeout_ms)

            return result
        finally:
            # Immediately disable Runtime (high-risk)
            self.release_domain('Runtime')

    def get_domain_status(self) -> Dict[str, str]:
        """Get status of all tracked domains"""
        with self._lock:
            return {
                domain: usage.state.name
                for domain, usage in self._domains.items()
            }


class RuntimeDomainContext:
    """Context manager for domain usage"""

    def __init__(self, manager: RuntimeDomainManager, domain: str):
        self._manager = manager
        self._domain = domain

    def __enter__(self):
        self._manager.require_domain(self._domain)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._manager.release_domain(self._domain)
        return False


# ==================== 2. CDP COMMAND PATTERN OBFUSCATION ====================

@dataclass
class CommandTiming:
    """Timing info for command obfuscation"""
    command: str
    timestamp: datetime
    duration_ms: int


class CommandObfuscator:
    """
    Obfuscates CDP command patterns to avoid detection

    Features:
    - Randomize domain enable order
    - Human-like delays between commands
    - Command batching where possible
    - Pattern breaking
    """

    def __init__(self):
        self._command_history: deque = deque(maxlen=100)
        self._lock = threading.Lock()

        # Delay configurations (in ms)
        self._min_delay_ms = 50
        self._max_delay_ms = 300
        self._exponential_base = 1.5

        # Commands that should have longer delays
        self._slow_commands: Set[str] = {
            'Page.navigate',
            'Runtime.evaluate',
            'DOM.getDocument',
            'Network.enable',
        }

        # Pattern detection scores
        self._pattern_scores: Dict[str, int] = {}

    def get_command_delay(self, command: str) -> float:
        """
        Get human-like delay before executing command
        Uses exponential backoff for repeated commands
        """
        with self._lock:
            # Count recent occurrences of this command
            recent_count = sum(
                1 for c in self._command_history
                if c.command == command and
                (datetime.now() - c.timestamp).total_seconds() < 5
            )

        # Base delay with randomization
        if command in self._slow_commands:
            base_delay = random.uniform(100, 300)
        else:
            base_delay = random.uniform(self._min_delay_ms, self._max_delay_ms)

        # Apply exponential backoff for repeated commands
        if recent_count > 0:
            backoff = self._exponential_base ** min(recent_count, 5)
            base_delay *= backoff

        # Add human-like jitter (Gaussian distribution)
        jitter = random.gauss(0, base_delay * 0.1)
        final_delay = max(10, base_delay + jitter)

        return final_delay / 1000  # Convert to seconds

    def record_command(self, command: str, duration_ms: int):
        """Record command execution for pattern analysis"""
        with self._lock:
            self._command_history.append(CommandTiming(
                command=command,
                timestamp=datetime.now(),
                duration_ms=duration_ms
            ))

    def randomize_domain_order(self, domains: List[str]) -> List[str]:
        """
        Randomize domain enable order while respecting dependencies
        """
        # Define soft dependencies (prefer to enable first)
        soft_deps = {
            'Runtime': [],
            'DOM': ['Runtime'],
            'Network': [],
            'Page': [],
            'Input': ['DOM'],
            'Emulation': [],
        }

        # Group domains by dependency level
        levels: Dict[int, List[str]] = {}

        for domain in domains:
            deps = soft_deps.get(domain, [])
            level = max([domains.index(d) for d in deps if d in domains], default=-1) + 1
            if level not in levels:
                levels[level] = []
            levels[level].append(domain)

        # Shuffle within each level and concatenate
        result = []
        for level in sorted(levels.keys()):
            level_domains = levels[level]
            random.shuffle(level_domains)
            result.extend(level_domains)

        return result

    def should_batch_commands(self, commands: List[str]) -> bool:
        """Check if commands should be batched"""
        # Batch non-critical commands to reduce pattern detection
        batchable = {
            'Network.clearBrowserCache',
            'Network.clearBrowserCookies',
            'Emulation.setDeviceMetricsOverride',
            'Emulation.setUserAgentOverride',
        }

        return all(cmd.split('.')[0] + '.' + cmd.split('.')[1] in batchable for cmd in commands)

    def get_pattern_score(self) -> int:
        """
        Calculate pattern detection risk score (0-100)
        Higher = more likely to be detected
        """
        score = 0

        with self._lock:
            if not self._command_history:
                return 0

            commands = [c.command for c in self._command_history]

            # Check for suspicious patterns

            # 1. Too many Runtime.evaluate in short time
            runtime_count = sum(1 for c in commands[-10:] if 'Runtime' in c)
            if runtime_count > 5:
                score += 20

            # 2. Rapid sequential commands
            if len(self._command_history) >= 2:
                recent = list(self._command_history)[-10:]
                for i in range(1, len(recent)):
                    gap = (recent[i].timestamp - recent[i-1].timestamp).total_seconds()
                    if gap < 0.05:  # Less than 50ms
                        score += 5

            # 3. Predictable command sequences
            # (e.g., always Page.navigate -> DOM.getDocument -> Runtime.evaluate)
            common_sequences = [
                ['Page.navigate', 'DOM.getDocument', 'Runtime.evaluate'],
                ['Runtime.enable', 'Runtime.evaluate', 'Runtime.disable'],
            ]

            for seq in common_sequences:
                if self._has_sequence(commands, seq):
                    score += 15

        return min(100, score)

    def _has_sequence(self, commands: List[str], sequence: List[str]) -> bool:
        """Check if command list contains a sequence"""
        if len(sequence) > len(commands):
            return False

        for i in range(len(commands) - len(sequence) + 1):
            if commands[i:i+len(sequence)] == sequence:
                return True

        return False


# ==================== 3. WEBRTC & MEDIA DEVICE LEAK PREVENTION ====================

@dataclass
class WebRTCConfig:
    """WebRTC leak prevention configuration"""
    disable_webrtc: bool = False
    ip_handling_policy: str = 'disable_non_proxied_udp'
    mock_media_devices: bool = True
    block_ice_candidates: bool = True


class WebRTCProtection:
    """
    Prevents WebRTC IP leaks and media device fingerprinting
    """

    def __init__(self, session, config: WebRTCConfig = None):
        self._session = session
        self.config = config or WebRTCConfig()
        self._protection_enabled = False

    def enable_protection(self) -> bool:
        """Enable WebRTC protection"""
        if self._protection_enabled:
            return True

        success = True

        # 1. Override WebRTC IP handling via CDP
        if self.config.ip_handling_policy:
            # This needs to be set via browser launch flags typically
            # But we can intercept and block ICE candidates
            pass

        # 2. Block/modify ICE candidates
        if self.config.block_ice_candidates:
            script = '''
                (function() {
                    // Store original methods
                    const origRTCPeerConnection = window.RTCPeerConnection;
                    const origWebkitRTCPeerConnection = window.webkitRTCPeerConnection;

                    function wrapPeerConnection(PC) {
                        if (!PC) return PC;

                        return function(config, constraints) {
                            // Modify ICE servers
                            if (config && config.iceServers) {
                                // Remove STUN/TURN servers that could leak IP
                                config.iceServers = config.iceServers.filter(server => {
                                    const urls = server.urls || server.url;
                                    if (!urls) return false;
                                    const urlArray = Array.isArray(urls) ? urls : [urls];
                                    return !urlArray.some(u => u.includes('stun:') || u.includes('turn:'));
                                });
                            }

                            const pc = new PC(config, constraints);

                            // Wrap onicecandidate
                            const origOnIceCandidate = Object.getOwnPropertyDescriptor(
                                pc.__proto__, 'onicecandidate'
                            );

                            Object.defineProperty(pc, 'onicecandidate', {
                                get: function() {
                                    return this._wrappedOnIceCandidate;
                                },
                                set: function(handler) {
                                    this._wrappedOnIceCandidate = function(event) {
                                        if (event.candidate) {
                                            // Filter out candidates that could leak real IP
                                            const candidate = event.candidate.candidate;
                                            if (candidate && (
                                                candidate.includes('srflx') ||  // Server reflexive
                                                candidate.includes('relay') ||  // TURN relay
                                                /([0-9]{1,3}\\.){3}[0-9]{1,3}/.test(candidate)  // IPv4
                                            )) {
                                                return; // Block this candidate
                                            }
                                        }
                                        if (handler) handler(event);
                                    };
                                }
                            });

                            return pc;
                        };
                    }

                    window.RTCPeerConnection = wrapPeerConnection(origRTCPeerConnection);
                    if (origWebkitRTCPeerConnection) {
                        window.webkitRTCPeerConnection = wrapPeerConnection(origWebkitRTCPeerConnection);
                    }

                    return true;
                })();
            '''

            try:
                result = self._session.evaluate_js(script)
                success = success and result.success
            except Exception:
                success = False

        # 3. Mock media devices
        if self.config.mock_media_devices:
            script = '''
                (function() {
                    // Mock navigator.mediaDevices
                    const mockDevices = [
                        {deviceId: 'default', groupId: 'default', kind: 'audioinput', label: ''},
                        {deviceId: 'default', groupId: 'default', kind: 'videoinput', label: ''},
                        {deviceId: 'default', groupId: 'default', kind: 'audiooutput', label: ''}
                    ];

                    if (navigator.mediaDevices) {
                        navigator.mediaDevices.enumerateDevices = async function() {
                            return mockDevices;
                        };

                        // Block getUserMedia
                        navigator.mediaDevices.getUserMedia = async function(constraints) {
                            throw new DOMException(
                                'Permission denied',
                                'NotAllowedError'
                            );
                        };
                    }

                    return true;
                })();
            '''

            try:
                result = self._session.evaluate_js(script)
                success = success and result.success
            except Exception:
                success = False

        self._protection_enabled = success
        return success

    def check_for_leaks(self) -> Dict[str, Any]:
        """Check if WebRTC is leaking real IP"""
        script = '''
            (function() {
                return new Promise((resolve) => {
                    const candidates = [];
                    const pc = new RTCPeerConnection({
                        iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
                    });

                    pc.createDataChannel('');

                    pc.onicecandidate = (e) => {
                        if (e.candidate) {
                            candidates.push(e.candidate.candidate);
                        }
                    };

                    pc.onicegatheringstatechange = () => {
                        if (pc.iceGatheringState === 'complete') {
                            pc.close();
                            resolve({candidates: candidates});
                        }
                    };

                    pc.createOffer().then(offer => pc.setLocalDescription(offer));

                    // Timeout after 5 seconds
                    setTimeout(() => {
                        pc.close();
                        resolve({candidates: candidates, timeout: true});
                    }, 5000);
                });
            })();
        '''

        try:
            result = self._session.evaluate_js(script, await_promise=True, timeout_ms=10000)
            if result.success and result.result:
                return result.result.get('result', {}).get('value', {})
        except Exception:
            pass

        return {'error': 'Check failed'}


# ==================== 4. SERVICE WORKER & FETCH HARDENING ====================

@dataclass
class ServiceWorkerInfo:
    """Information about a registered service worker"""
    registration_id: str
    scope_url: str
    is_active: bool
    version_id: Optional[str] = None


class ServiceWorkerManager:
    """
    Manages Service Workers to prevent cache issues and detection
    """

    def __init__(self, session):
        self._session = session
        self._workers: Dict[str, ServiceWorkerInfo] = {}
        self._event_handlers: List[Callable] = []
        self._lock = threading.Lock()

    def enable_monitoring(self) -> bool:
        """Start monitoring service workers"""
        try:
            # Enable ServiceWorker domain
            result = self._session.send_command('ServiceWorker.enable')
            if not result.success:
                return False

            # Set auto-attach for early interception
            result = self._session.send_command('Target.setAutoAttach', {
                'autoAttach': True,
                'waitForDebuggerOnStart': False,
                'flatten': True
            })

            return result.success
        except Exception:
            return False

    def disable_monitoring(self):
        """Stop monitoring service workers"""
        try:
            self._session.send_command('ServiceWorker.disable')
        except Exception:
            pass

    def get_all_workers(self) -> List[ServiceWorkerInfo]:
        """Get all registered service workers"""
        try:
            result = self._session.send_command('ServiceWorker.getRegistrations')
            if result.success and result.result:
                workers = []
                for reg in result.result.get('registrations', []):
                    workers.append(ServiceWorkerInfo(
                        registration_id=reg.get('registrationId', ''),
                        scope_url=reg.get('scopeURL', ''),
                        is_active=reg.get('isDeleted', False) == False
                    ))
                return workers
        except Exception:
            pass

        return []

    def unregister_worker(self, scope_url: str) -> bool:
        """Unregister a service worker by scope"""
        script = f'''
            (async function() {{
                try {{
                    const registrations = await navigator.serviceWorker.getRegistrations();
                    for (const reg of registrations) {{
                        if (reg.scope === '{scope_url}' || '{scope_url}' === '*') {{
                            await reg.unregister();
                        }}
                    }}
                    return true;
                }} catch (e) {{
                    return false;
                }}
            }})();
        '''

        try:
            result = self._session.evaluate_js(script, await_promise=True)
            return result.success
        except Exception:
            return False

    def unregister_all_workers(self) -> bool:
        """Unregister all service workers"""
        return self.unregister_worker('*')

    def bypass_cache(self) -> bool:
        """Bypass service worker cache"""
        try:
            # Set bypass for network
            result = self._session.send_command('Network.setBypassServiceWorker', {
                'bypass': True
            })
            return result.success
        except Exception:
            return False

    def intercept_fetch(self, patterns: List[str] = None) -> bool:
        """
        Set up Fetch interception for modifying requests
        """
        patterns = patterns or ['*']

        try:
            result = self._session.send_command('Fetch.enable', {
                'patterns': [{'urlPattern': p} for p in patterns]
            })
            return result.success
        except Exception:
            return False

    def disable_fetch_interception(self):
        """Disable Fetch interception"""
        try:
            self._session.send_command('Fetch.disable')
        except Exception:
            pass


# ==================== 5. MEMORY & DOM LEAK MONITORING ====================

@dataclass
class MemoryMetrics:
    """Memory usage metrics"""
    js_heap_size_used: int = 0
    js_heap_size_total: int = 0
    dom_node_count: int = 0
    document_count: int = 0
    js_event_listener_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryThresholds:
    """Thresholds for memory warnings"""
    js_heap_warning_mb: int = 200
    js_heap_critical_mb: int = 500
    dom_nodes_warning: int = 10000
    dom_nodes_critical: int = 50000
    event_listeners_warning: int = 1000
    event_listeners_critical: int = 5000


class MemoryMonitor:
    """
    Monitors memory and DOM to prevent leaks during long-running sessions
    """

    def __init__(self, session, thresholds: MemoryThresholds = None):
        self._session = session
        self.thresholds = thresholds or MemoryThresholds()

        self._metrics_history: deque = deque(maxlen=1000)
        self._lock = threading.Lock()

        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()
        self._monitor_interval_ms = 30000  # Check every 30 seconds

        # Callbacks
        self._on_warning: Optional[Callable[[str, MemoryMetrics], None]] = None
        self._on_critical: Optional[Callable[[str, MemoryMetrics], None]] = None

    def start_monitoring(self, interval_ms: int = 30000):
        """Start background memory monitoring"""
        self._monitor_interval_ms = interval_ms
        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop memory monitoring"""
        self._stop_monitor.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)

    def _monitor_loop(self):
        """Background monitoring loop"""
        while not self._stop_monitor.is_set():
            time.sleep(self._monitor_interval_ms / 1000)

            if self._stop_monitor.is_set():
                break

            metrics = self.get_current_metrics()
            if metrics:
                self._check_thresholds(metrics)

    def get_current_metrics(self) -> Optional[MemoryMetrics]:
        """Get current memory metrics"""
        metrics = MemoryMetrics()

        try:
            # Get JS heap info via Performance.getMetrics
            result = self._session.send_command('Performance.getMetrics')
            if result.success and result.result:
                for metric in result.result.get('metrics', []):
                    name = metric.get('name', '')
                    value = metric.get('value', 0)

                    if name == 'JSHeapUsedSize':
                        metrics.js_heap_size_used = int(value)
                    elif name == 'JSHeapTotalSize':
                        metrics.js_heap_size_total = int(value)
                    elif name == 'Nodes':
                        metrics.dom_node_count = int(value)
                    elif name == 'Documents':
                        metrics.document_count = int(value)
                    elif name == 'JSEventListeners':
                        metrics.js_event_listener_count = int(value)

            # Store in history
            with self._lock:
                self._metrics_history.append(metrics)

            return metrics

        except Exception:
            return None

    def get_dom_counters(self) -> Dict[str, int]:
        """Get detailed DOM counters"""
        try:
            result = self._session.send_command('Memory.getDOMCounters')
            if result.success and result.result:
                return {
                    'nodes': result.result.get('nodes', 0),
                    'documents': result.result.get('documents', 0),
                    'jsEventListeners': result.result.get('jsEventListeners', 0)
                }
        except Exception:
            pass

        return {}

    def force_garbage_collection(self) -> bool:
        """Force JavaScript garbage collection"""
        try:
            # Method 1: Memory.forciblyPurgeJavaScriptMemory
            result = self._session.send_command('Memory.forciblyPurgeJavaScriptMemory')
            if result.success:
                return True

            # Method 2: HeapProfiler.collectGarbage
            result = self._session.send_command('HeapProfiler.collectGarbage')
            return result.success

        except Exception:
            return False

    def _check_thresholds(self, metrics: MemoryMetrics):
        """Check metrics against thresholds"""
        heap_mb = metrics.js_heap_size_used / (1024 * 1024)

        # Check JS Heap
        if heap_mb >= self.thresholds.js_heap_critical_mb:
            if self._on_critical:
                self._on_critical('js_heap_critical', metrics)
            # Auto-GC on critical
            self.force_garbage_collection()
        elif heap_mb >= self.thresholds.js_heap_warning_mb:
            if self._on_warning:
                self._on_warning('js_heap_warning', metrics)

        # Check DOM nodes
        if metrics.dom_node_count >= self.thresholds.dom_nodes_critical:
            if self._on_critical:
                self._on_critical('dom_nodes_critical', metrics)
        elif metrics.dom_node_count >= self.thresholds.dom_nodes_warning:
            if self._on_warning:
                self._on_warning('dom_nodes_warning', metrics)

        # Check event listeners
        if metrics.js_event_listener_count >= self.thresholds.event_listeners_critical:
            if self._on_critical:
                self._on_critical('event_listeners_critical', metrics)
        elif metrics.js_event_listener_count >= self.thresholds.event_listeners_warning:
            if self._on_warning:
                self._on_warning('event_listeners_warning', metrics)

    def get_metrics_history(self) -> List[MemoryMetrics]:
        """Get metrics history"""
        with self._lock:
            return list(self._metrics_history)

    def get_summary(self) -> Dict[str, Any]:
        """Get memory summary"""
        current = self.get_current_metrics()

        if not current:
            return {'error': 'Could not get metrics'}

        return {
            'current': {
                'js_heap_mb': round(current.js_heap_size_used / (1024 * 1024), 2),
                'dom_nodes': current.dom_node_count,
                'event_listeners': current.js_event_listener_count,
                'documents': current.document_count
            },
            'thresholds': {
                'js_heap_warning_mb': self.thresholds.js_heap_warning_mb,
                'js_heap_critical_mb': self.thresholds.js_heap_critical_mb,
                'dom_nodes_warning': self.thresholds.dom_nodes_warning,
                'event_listeners_warning': self.thresholds.event_listeners_warning
            },
            'history_count': len(self._metrics_history)
        }


# ==================== 6. ISOLATED WORLD CONSISTENCY ====================

@dataclass
class ExecutionContext:
    """Represents a JavaScript execution context"""
    context_id: int
    frame_id: str
    world_name: str
    is_default: bool
    origin: str = ''
    created_at: datetime = field(default_factory=datetime.now)


class IsolatedWorldManager:
    """
    Manages isolated worlds for consistent script injection

    Key features:
    - Track context creation/destruction
    - Pin to specific world for injections
    - Avoid stale context errors
    """

    ISOLATED_WORLD_NAME = 'CDP_ISOLATED_WORLD'

    def __init__(self, session):
        self._session = session
        self._contexts: Dict[int, ExecutionContext] = {}
        self._frame_contexts: Dict[str, List[int]] = {}  # frame_id -> context_ids
        self._isolated_world_id: Optional[int] = None
        self._lock = threading.Lock()

        # Event handlers
        self._context_created_handlers: List[Callable] = []
        self._context_destroyed_handlers: List[Callable] = []

    def initialize(self) -> bool:
        """Initialize world tracking"""
        try:
            # Enable Runtime to track contexts
            result = self._session.send_command('Runtime.enable')
            return result.success
        except Exception:
            return False

    def on_execution_context_created(self, params: Dict):
        """Handle Runtime.executionContextCreated event"""
        context_data = params.get('context', {})

        context = ExecutionContext(
            context_id=context_data.get('id', 0),
            frame_id=context_data.get('auxData', {}).get('frameId', ''),
            world_name=context_data.get('name', ''),
            is_default=context_data.get('auxData', {}).get('isDefault', False),
            origin=context_data.get('origin', '')
        )

        with self._lock:
            self._contexts[context.context_id] = context

            # Track by frame
            if context.frame_id:
                if context.frame_id not in self._frame_contexts:
                    self._frame_contexts[context.frame_id] = []
                self._frame_contexts[context.frame_id].append(context.context_id)

            # Check if this is our isolated world
            if context.world_name == self.ISOLATED_WORLD_NAME:
                self._isolated_world_id = context.context_id

        # Notify handlers
        for handler in self._context_created_handlers:
            try:
                handler(context)
            except Exception:
                pass

    def on_execution_context_destroyed(self, params: Dict):
        """Handle Runtime.executionContextDestroyed event"""
        context_id = params.get('executionContextId', 0)

        with self._lock:
            if context_id in self._contexts:
                context = self._contexts.pop(context_id)

                # Remove from frame tracking
                if context.frame_id in self._frame_contexts:
                    if context_id in self._frame_contexts[context.frame_id]:
                        self._frame_contexts[context.frame_id].remove(context_id)

                # Clear isolated world ref if it was destroyed
                if self._isolated_world_id == context_id:
                    self._isolated_world_id = None

        # Notify handlers
        for handler in self._context_destroyed_handlers:
            try:
                handler(context_id)
            except Exception:
                pass

    def on_execution_contexts_cleared(self, params: Dict):
        """Handle Runtime.executionContextsCleared event"""
        with self._lock:
            self._contexts.clear()
            self._frame_contexts.clear()
            self._isolated_world_id = None

    def create_isolated_world(self, frame_id: str = None) -> Optional[int]:
        """
        Create an isolated world for script injection
        Returns the execution context ID
        """
        try:
            # Get main frame if not specified
            if not frame_id:
                result = self._session.send_command('Page.getFrameTree')
                if result.success and result.result:
                    frame_id = result.result.get('frameTree', {}).get('frame', {}).get('id')

            if not frame_id:
                return None

            # Create isolated world
            result = self._session.send_command('Page.createIsolatedWorld', {
                'frameId': frame_id,
                'worldName': self.ISOLATED_WORLD_NAME,
                'grantUniveralAccess': True
            })

            if result.success and result.result:
                context_id = result.result.get('executionContextId')
                with self._lock:
                    self._isolated_world_id = context_id
                return context_id

        except Exception:
            pass

        return None

    def get_isolated_context_id(self) -> Optional[int]:
        """Get the isolated world context ID, creating if needed"""
        with self._lock:
            if self._isolated_world_id and self._isolated_world_id in self._contexts:
                return self._isolated_world_id

        # Need to create new isolated world
        return self.create_isolated_world()

    def evaluate_in_isolated(self, expression: str, timeout_ms: int = 5000) -> Any:
        """
        Evaluate expression in isolated world
        Ensures consistent context and avoids main world detection
        """
        context_id = self.get_isolated_context_id()

        if not context_id:
            # Fallback to main world
            return self._session.evaluate_js(expression, timeout_ms=timeout_ms)

        try:
            result = self._session.send_command('Runtime.evaluate', {
                'expression': expression,
                'contextId': context_id,
                'returnByValue': True,
                'awaitPromise': False
            }, timeout_ms=timeout_ms)

            return result

        except Exception as e:
            # Context may have been destroyed, try recreating
            self._isolated_world_id = None
            return self._session.evaluate_js(expression, timeout_ms=timeout_ms)

    def get_main_context(self, frame_id: str = None) -> Optional[ExecutionContext]:
        """Get the main (default) execution context for a frame"""
        with self._lock:
            for context in self._contexts.values():
                if context.is_default:
                    if not frame_id or context.frame_id == frame_id:
                        return context
        return None

    def is_context_valid(self, context_id: int) -> bool:
        """Check if a context ID is still valid"""
        with self._lock:
            return context_id in self._contexts

    def get_context_status(self) -> Dict[str, Any]:
        """Get status of all contexts"""
        with self._lock:
            return {
                'total_contexts': len(self._contexts),
                'isolated_world_id': self._isolated_world_id,
                'frames': len(self._frame_contexts),
                'contexts': [
                    {
                        'id': ctx.context_id,
                        'frame': ctx.frame_id,
                        'world': ctx.world_name,
                        'is_default': ctx.is_default
                    }
                    for ctx in self._contexts.values()
                ]
            }


# ==================== STEALTH MANAGER (UNIFIED) ====================

class StealthManager:
    """
    Unified stealth manager combining all anti-detection features
    """

    def __init__(self, session):
        self._session = session

        # Initialize all components
        self.runtime_manager = RuntimeDomainManager(session)
        self.command_obfuscator = CommandObfuscator()
        self.webrtc_protection = WebRTCProtection(session)
        self.service_worker_manager = ServiceWorkerManager(session)
        self.memory_monitor = MemoryMonitor(session)
        self.isolated_world_manager = IsolatedWorldManager(session)

        self._enabled = False

    def enable_all(self) -> Dict[str, bool]:
        """Enable all stealth features"""
        results = {}

        # 1. Start runtime domain management
        self.runtime_manager.start_cleanup_thread()
        results['runtime_domain_manager'] = True

        # 2. WebRTC protection
        results['webrtc_protection'] = self.webrtc_protection.enable_protection()

        # 3. Service worker management
        results['service_worker_manager'] = self.service_worker_manager.enable_monitoring()

        # 4. Memory monitoring
        self.memory_monitor.start_monitoring()
        results['memory_monitor'] = True

        # 5. Isolated world management
        results['isolated_world_manager'] = self.isolated_world_manager.initialize()

        self._enabled = True
        return results

    def disable_all(self):
        """Disable all stealth features"""
        self.runtime_manager.stop_cleanup_thread()
        self.service_worker_manager.disable_monitoring()
        self.memory_monitor.stop_monitoring()
        self._enabled = False

    def get_stealth_status(self) -> Dict[str, Any]:
        """Get status of all stealth features"""
        return {
            'enabled': self._enabled,
            'runtime_domains': self.runtime_manager.get_domain_status(),
            'pattern_score': self.command_obfuscator.get_pattern_score(),
            'memory': self.memory_monitor.get_summary(),
            'isolated_worlds': self.isolated_world_manager.get_context_status()
        }

    def evaluate_stealth(self, expression: str, timeout_ms: int = 5000) -> Any:
        """
        Evaluate JS with minimal footprint:
        - Uses isolated world
        - Minimal Runtime domain exposure
        - Human-like delay
        """
        # Add command delay
        delay = self.command_obfuscator.get_command_delay('Runtime.evaluate')
        time.sleep(delay)

        # Use isolated world if available
        result = self.isolated_world_manager.evaluate_in_isolated(expression, timeout_ms)

        # Record command
        if result:
            self.command_obfuscator.record_command('Runtime.evaluate', timeout_ms)

        return result
