"""
Automation Engine - Production-grade architecture
State Machine + Condition Wait + Verify + Artifact + Isolation
Human-like behavior built-in
"""
from .engine import AutomationEngine, JobState, StateResult, FailureType
from .cdp_client import CDPClient, Condition, ConditionType, WaitResult, ActionResult
from .artifacts import ArtifactCollector, JobArtifact
from .jobs import Job, JobContext, JobResult
from .human_behavior import HumanBehavior, AntiDetection, WaitStrategy

__all__ = [
    # Engine
    'AutomationEngine',
    'JobState',
    'StateResult',
    'FailureType',
    # CDP Client
    'CDPClient',
    'Condition',
    'ConditionType',
    'WaitResult',
    'ActionResult',
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
]
