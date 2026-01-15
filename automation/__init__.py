"""
Automation Engine - Production-grade architecture
State Machine + Condition Wait + Verify + Artifact + Isolation
Human-like behavior built-in

CDP MAX: Production-grade CDP implementation with 12 MAX features
"""
from .engine import AutomationEngine, JobState, StateResult, FailureType
from .cdp_client import CDPClient, Condition, ConditionType, WaitResult, ActionResult
from .artifacts import ArtifactCollector, JobArtifact
from .jobs import Job, JobContext, JobResult
from .human_behavior import HumanBehavior, AntiDetection, WaitStrategy

# CDP MAX - Production-grade CDP
from .cdp_max import (
    CDPClientMAX, CDPClientConfig,
    CDPSession, SessionState, SessionConfig,
    Locator, LocatorType, SelectorEngine,
    WaitEngine, WaitCondition, DOMCondition,
    ActionExecutor, ActionResult as ActionResultMAX, Precondition, Postcondition,
    NavigationManager, NavigationResult,
    RecoveryManager, RecoveryLevel,
    Watchdog, WatchdogConfig,
    ObservabilityEngine, ReasonCode, FailureReason,
    # Stealth (anti-detection)
    StealthManager,
    RuntimeDomainManager,
    WebRTCProtection, WebRTCConfig,
    ServiceWorkerManager,
    MemoryMonitor, MemoryMetrics, MemoryThresholds,
    IsolatedWorldManager
)

__all__ = [
    # Engine
    'AutomationEngine',
    'JobState',
    'StateResult',
    'FailureType',
    # CDP Client (legacy)
    'CDPClient',
    'Condition',
    'ConditionType',
    'WaitResult',
    'ActionResult',
    # CDP MAX (new)
    'CDPClientMAX', 'CDPClientConfig',
    'CDPSession', 'SessionState', 'SessionConfig',
    'Locator', 'LocatorType', 'SelectorEngine',
    'WaitEngine', 'WaitCondition', 'DOMCondition',
    'ActionExecutor', 'ActionResultMAX', 'Precondition', 'Postcondition',
    'NavigationManager', 'NavigationResult',
    'RecoveryManager', 'RecoveryLevel',
    'Watchdog', 'WatchdogConfig',
    'ObservabilityEngine', 'ReasonCode', 'FailureReason',
    # Stealth (anti-detection)
    'StealthManager',
    'RuntimeDomainManager',
    'WebRTCProtection', 'WebRTCConfig',
    'ServiceWorkerManager',
    'MemoryMonitor', 'MemoryMetrics', 'MemoryThresholds',
    'IsolatedWorldManager',
    # Artifacts
    'ArtifactCollector',
    'JobArtifact',
    # Jobs
    'Job',
    'JobContext',
    'JobResult',
    # Human Behavior
    'HumanBehavior',
    'AntiDetection',
    'WaitStrategy',
    # CDP Helper
    'CDPHelper',
    'CDPHelperResult',
    'create_cdp_helper',
    'get_remote_port_from_browser',
]

# CDP Helper - High-level automation for tabs
from .cdp_helper import CDPHelper, CDPHelperResult, create_cdp_helper, get_remote_port_from_browser
