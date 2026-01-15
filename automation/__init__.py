"""
Automation Engine - Production-grade architecture
State Machine + Condition Wait + Verify + Artifact + Isolation
"""
from .engine import AutomationEngine, JobState, StateResult
from .cdp_client import CDPClient, Condition, WaitResult
from .artifacts import ArtifactCollector
from .jobs import Job, JobContext, JobResult

__all__ = [
    'AutomationEngine',
    'JobState',
    'StateResult',
    'CDPClient',
    'Condition',
    'WaitResult',
    'ArtifactCollector',
    'Job',
    'JobContext',
    'JobResult'
]
