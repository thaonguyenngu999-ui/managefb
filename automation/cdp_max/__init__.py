"""
CDP MAX - Production-grade Chrome DevTools Protocol implementation

12 MAX checklist implementation:
1. Connection layer MAX - Auto-reconnect, heartbeat, target management, backpressure
2. Deterministic waiting MAX - Multi-source conditions, timeout tiers, stability window
3. Action layer MAX - Pre/postcondition, idempotent guards, atomicity
4. Selector strategy MAX - Semantic priority, scoped search, frame-safe
5. Event-driven MAX - CDP event subscription, event-based sync
6. Navigation correctness MAX - SPA handling, redirect detection
7. File I/O MAX - Upload/download handling
8. Concurrency model MAX - Per-target serialization, worker quota
9. Recovery MAX - Multi-tier recovery system
10. Crash/Freeze containment MAX - Watchdog, hard timeout, poisoned context
11. Performance MAX - Command batching, locator caching
12. Observability MAX - Machine-readable reason codes

Stealth features (anti-detection):
- Runtime domain minimization & side-effect mitigation
- CDP command pattern obfuscation & rate limiting
- WebRTC & media device leak prevention
- Service Worker & Fetch interception hardening
- Memory & DOM leak monitoring
- Isolated world consistency & world pinning
"""

from .session import CDPSession, SessionState, SessionConfig
from .events import EventEmitter, CDPEvent, EventType
from .targets import TargetManager, Target, TargetType
from .waits import (
    WaitEngine, WaitCondition, WaitResult,
    DOMCondition, NetworkCondition, StabilityCondition
)
from .actions import (
    ActionExecutor, ActionResult, ActionType,
    Precondition, Postcondition
)
from .selectors import (
    SelectorEngine, Locator, LocatorType,
    ScopedLocator, FrameContext
)
from .navigation import NavigationManager, NavigationType, NavigationResult
from .file_io import FileIOManager, UploadResult, DownloadResult
from .concurrency import (
    ConcurrencyManager, JobQueue, WorkerPool,
    CommandThrottle
)
from .recovery import (
    RecoveryManager, RecoveryLevel, RecoveryResult,
    SafeResetPoint
)
from .watchdog import Watchdog, WatchdogConfig, HealthStatus
from .performance import PerformanceOptimizer, CommandBatcher, LocatorCache
from .observability import (
    ObservabilityEngine, ReasonCode, FailureReason,
    StepTrace, JobTrace
)
from .client import CDPClientMAX, CDPClientConfig
from .stealth import (
    StealthManager,
    RuntimeDomainManager, RuntimeDomainContext,
    CommandObfuscator,
    WebRTCProtection, WebRTCConfig,
    ServiceWorkerManager, ServiceWorkerInfo,
    MemoryMonitor, MemoryMetrics, MemoryThresholds,
    IsolatedWorldManager, ExecutionContext
)

__all__ = [
    # Session
    'CDPSession', 'SessionState', 'SessionConfig',
    # Events
    'EventEmitter', 'CDPEvent', 'EventType',
    # Targets
    'TargetManager', 'Target', 'TargetType',
    # Waits
    'WaitEngine', 'WaitCondition', 'WaitResult',
    'DOMCondition', 'NetworkCondition', 'StabilityCondition',
    # Actions
    'ActionExecutor', 'ActionResult', 'ActionType',
    'Precondition', 'Postcondition',
    # Selectors
    'SelectorEngine', 'Locator', 'LocatorType',
    'ScopedLocator', 'FrameContext',
    # Navigation
    'NavigationManager', 'NavigationType', 'NavigationResult',
    # File I/O
    'FileIOManager', 'UploadResult', 'DownloadResult',
    # Concurrency
    'ConcurrencyManager', 'JobQueue', 'WorkerPool', 'CommandThrottle',
    # Recovery
    'RecoveryManager', 'RecoveryLevel', 'RecoveryResult', 'SafeResetPoint',
    # Watchdog
    'Watchdog', 'WatchdogConfig', 'HealthStatus',
    # Performance
    'PerformanceOptimizer', 'CommandBatcher', 'LocatorCache',
    # Observability
    'ObservabilityEngine', 'ReasonCode', 'FailureReason',
    'StepTrace', 'JobTrace',
    # Client
    'CDPClientMAX',
    'CDPClientConfig',
    # Stealth (anti-detection)
    'StealthManager',
    'RuntimeDomainManager', 'RuntimeDomainContext',
    'CommandObfuscator',
    'WebRTCProtection', 'WebRTCConfig',
    'ServiceWorkerManager', 'ServiceWorkerInfo',
    'MemoryMonitor', 'MemoryMetrics', 'MemoryThresholds',
    'IsolatedWorldManager', 'ExecutionContext',
]
