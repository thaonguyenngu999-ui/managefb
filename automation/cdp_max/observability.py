"""
Observability MAX - Machine-readable reason codes and tracing

Every decision (retry/fail/skip) has a machine-readable reason.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import threading


class ReasonCode(Enum):
    """Machine-readable reason codes for every decision"""
    # Success codes
    SUCCESS = "SUCCESS"
    CONDITION_MET = "CONDITION_MET"
    ALREADY_DONE = "ALREADY_DONE"
    SKIPPED_IDEMPOTENT = "SKIPPED_IDEMPOTENT"

    # Timeout codes
    TIMEOUT_STEP = "TIMEOUT_STEP"
    TIMEOUT_STATE = "TIMEOUT_STATE"
    TIMEOUT_JOB = "TIMEOUT_JOB"
    TIMEOUT_NETWORK = "TIMEOUT_NETWORK"
    TIMEOUT_RENDER = "TIMEOUT_RENDER"

    # Element codes
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ELEMENT_NOT_VISIBLE = "ELEMENT_NOT_VISIBLE"
    ELEMENT_NOT_CLICKABLE = "ELEMENT_NOT_CLICKABLE"
    ELEMENT_STALE = "ELEMENT_STALE"
    ELEMENT_DETACHED = "ELEMENT_DETACHED"
    ELEMENT_COVERED = "ELEMENT_COVERED"

    # Navigation codes
    NAVIGATION_FAILED = "NAVIGATION_FAILED"
    NAVIGATION_TIMEOUT = "NAVIGATION_TIMEOUT"
    REDIRECT_LOOP = "REDIRECT_LOOP"
    UNEXPECTED_PAGE = "UNEXPECTED_PAGE"
    SPA_NOT_READY = "SPA_NOT_READY"

    # Network codes
    NETWORK_ERROR = "NETWORK_ERROR"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    REQUEST_FAILED = "REQUEST_FAILED"
    RESPONSE_ERROR = "RESPONSE_ERROR"

    # CDP codes
    CDP_DISCONNECTED = "CDP_DISCONNECTED"
    CDP_RECONNECTING = "CDP_RECONNECTING"
    CDP_RECONNECT_FAILED = "CDP_RECONNECT_FAILED"
    CDP_COMMAND_FAILED = "CDP_COMMAND_FAILED"
    CDP_PROTOCOL_ERROR = "CDP_PROTOCOL_ERROR"

    # Browser codes
    BROWSER_CRASHED = "BROWSER_CRASHED"
    BROWSER_HUNG = "BROWSER_HUNG"
    BROWSER_NOT_RESPONDING = "BROWSER_NOT_RESPONDING"
    TARGET_CLOSED = "TARGET_CLOSED"
    TARGET_CRASHED = "TARGET_CRASHED"

    # Logic codes
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    POSTCONDITION_FAILED = "POSTCONDITION_FAILED"
    GUARD_REJECTED = "GUARD_REJECTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"

    # Recovery codes
    RETRY_STEP = "RETRY_STEP"
    RETRY_STATE = "RETRY_STATE"
    RECREATE_CONTEXT = "RECREATE_CONTEXT"
    RESTART_BROWSER = "RESTART_BROWSER"
    RECOVERY_EXHAUSTED = "RECOVERY_EXHAUSTED"

    # Concurrency codes
    QUEUE_FULL = "QUEUE_FULL"
    THROTTLED = "THROTTLED"
    WORKER_BUSY = "WORKER_BUSY"

    # File codes
    UPLOAD_FAILED = "UPLOAD_FAILED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    FILE_NOT_READY = "FILE_NOT_READY"

    # System codes
    SYSTEM_ERROR = "SYSTEM_ERROR"
    MEMORY_PRESSURE = "MEMORY_PRESSURE"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"


@dataclass
class FailureReason:
    """Detailed failure reason with context"""
    code: ReasonCode
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    suggested_action: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'code': self.code.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'context': self.context,
            'recoverable': self.recoverable,
            'suggested_action': self.suggested_action
        }

    @classmethod
    def from_exception(cls, e: Exception, code: ReasonCode = ReasonCode.SYSTEM_ERROR) -> 'FailureReason':
        import traceback
        return cls(
            code=code,
            message=str(e),
            context={'exception_type': type(e).__name__, 'traceback': traceback.format_exc()},
            recoverable=False
        )


@dataclass
class StepTrace:
    """Trace for a single step/action"""
    step_id: str
    step_type: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: int = 0
    success: bool = False
    reason: Optional[FailureReason] = None
    input_data: Dict = field(default_factory=dict)
    output_data: Dict = field(default_factory=dict)
    retries: int = 0

    def complete(self, success: bool, reason: Optional[FailureReason] = None):
        self.end_time = datetime.now().isoformat()
        self.duration_ms = int((
            datetime.fromisoformat(self.end_time) -
            datetime.fromisoformat(self.start_time)
        ).total_seconds() * 1000)
        self.success = success
        self.reason = reason

    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'step_type': self.step_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'reason': self.reason.to_dict() if self.reason else None,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'retries': self.retries
        }


@dataclass
class JobTrace:
    """Complete trace for a job execution"""
    job_id: str
    job_type: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: int = 0
    success: bool = False
    final_reason: Optional[FailureReason] = None
    steps: List[StepTrace] = field(default_factory=list)
    state_history: List[Dict] = field(default_factory=list)
    recovery_attempts: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)

    def add_step(self, step: StepTrace):
        self.steps.append(step)

    def add_state_transition(self, from_state: str, to_state: str, reason: Optional[FailureReason] = None):
        self.state_history.append({
            'from': from_state,
            'to': to_state,
            'timestamp': datetime.now().isoformat(),
            'reason': reason.to_dict() if reason else None
        })

    def add_recovery_attempt(self, level: str, success: bool, reason: Optional[FailureReason] = None):
        self.recovery_attempts.append({
            'level': level,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'reason': reason.to_dict() if reason else None
        })

    def complete(self, success: bool, reason: Optional[FailureReason] = None):
        self.end_time = datetime.now().isoformat()
        self.duration_ms = int((
            datetime.fromisoformat(self.end_time) -
            datetime.fromisoformat(self.start_time)
        ).total_seconds() * 1000)
        self.success = success
        self.final_reason = reason

    def to_dict(self) -> Dict:
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'final_reason': self.final_reason.to_dict() if self.final_reason else None,
            'steps': [s.to_dict() for s in self.steps],
            'state_history': self.state_history,
            'recovery_attempts': self.recovery_attempts,
            'context': self.context
        }


class ObservabilityEngine:
    """
    Central observability engine for all CDP operations

    Responsibilities:
    - Track all operations with machine-readable codes
    - Maintain traces for debugging
    - Provide queryable history
    """

    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self._traces: Dict[str, JobTrace] = {}
        self._current_steps: Dict[str, StepTrace] = {}
        self._lock = threading.Lock()
        self._metrics: Dict[str, int] = {}

    def start_job(self, job_id: str, job_type: str, context: Dict = None) -> JobTrace:
        """Start tracing a job"""
        trace = JobTrace(
            job_id=job_id,
            job_type=job_type,
            start_time=datetime.now().isoformat(),
            context=context or {}
        )
        with self._lock:
            self._traces[job_id] = trace
            # Cleanup old traces if needed
            if len(self._traces) > self.max_traces:
                oldest = sorted(self._traces.keys())[0]
                del self._traces[oldest]
        return trace

    def start_step(self, job_id: str, step_id: str, step_type: str,
                   input_data: Dict = None) -> StepTrace:
        """Start tracing a step"""
        step = StepTrace(
            step_id=step_id,
            step_type=step_type,
            start_time=datetime.now().isoformat(),
            input_data=input_data or {}
        )
        with self._lock:
            self._current_steps[f"{job_id}:{step_id}"] = step
            if job_id in self._traces:
                self._traces[job_id].add_step(step)
        return step

    def complete_step(self, job_id: str, step_id: str, success: bool,
                      reason: Optional[FailureReason] = None,
                      output_data: Dict = None):
        """Complete a step trace"""
        key = f"{job_id}:{step_id}"
        with self._lock:
            if key in self._current_steps:
                step = self._current_steps[key]
                step.complete(success, reason)
                if output_data:
                    step.output_data = output_data
                del self._current_steps[key]

                # Update metrics
                metric_key = f"step_{step.step_type}_{'success' if success else 'fail'}"
                self._metrics[metric_key] = self._metrics.get(metric_key, 0) + 1

    def complete_job(self, job_id: str, success: bool,
                     reason: Optional[FailureReason] = None):
        """Complete a job trace"""
        with self._lock:
            if job_id in self._traces:
                self._traces[job_id].complete(success, reason)

                # Update metrics
                metric_key = f"job_{'success' if success else 'fail'}"
                self._metrics[metric_key] = self._metrics.get(metric_key, 0) + 1

    def record_state_transition(self, job_id: str, from_state: str, to_state: str,
                                reason: Optional[FailureReason] = None):
        """Record state machine transition"""
        with self._lock:
            if job_id in self._traces:
                self._traces[job_id].add_state_transition(from_state, to_state, reason)

    def record_recovery(self, job_id: str, level: str, success: bool,
                       reason: Optional[FailureReason] = None):
        """Record recovery attempt"""
        with self._lock:
            if job_id in self._traces:
                self._traces[job_id].add_recovery_attempt(level, success, reason)

    def get_trace(self, job_id: str) -> Optional[JobTrace]:
        """Get trace for a job"""
        return self._traces.get(job_id)

    def get_failed_jobs(self, limit: int = 50) -> List[JobTrace]:
        """Get recent failed jobs"""
        with self._lock:
            failed = [t for t in self._traces.values() if not t.success and t.end_time]
            return sorted(failed, key=lambda x: x.end_time or '', reverse=True)[:limit]

    def get_metrics(self) -> Dict[str, int]:
        """Get aggregated metrics"""
        with self._lock:
            return self._metrics.copy()

    def get_reason_distribution(self) -> Dict[str, int]:
        """Get distribution of failure reasons"""
        distribution: Dict[str, int] = {}
        with self._lock:
            for trace in self._traces.values():
                if trace.final_reason:
                    code = trace.final_reason.code.value
                    distribution[code] = distribution.get(code, 0) + 1
                for step in trace.steps:
                    if step.reason:
                        code = step.reason.code.value
                        distribution[code] = distribution.get(code, 0) + 1
        return distribution

    def export_traces(self, job_ids: List[str] = None) -> str:
        """Export traces as JSON"""
        with self._lock:
            if job_ids:
                traces = [self._traces[jid] for jid in job_ids if jid in self._traces]
            else:
                traces = list(self._traces.values())
        return json.dumps([t.to_dict() for t in traces], indent=2)


# Global observability instance
_observability: Optional[ObservabilityEngine] = None


def get_observability() -> ObservabilityEngine:
    """Get or create global observability engine"""
    global _observability
    if _observability is None:
        _observability = ObservabilityEngine()
    return _observability
