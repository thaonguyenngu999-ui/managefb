"""
State Machine Engine - Core automation controller
Each job runs through explicit states with entry/exit conditions
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import threading
import traceback


class JobState(Enum):
    """Explicit job states - each state does ONE thing only"""
    INIT = auto()           # Initialize job context
    OPEN_BROWSER = auto()   # Open browser/profile
    NAVIGATE = auto()       # Navigate to target URL
    READY_CHECK = auto()    # Check page is ready
    ACTION_PREPARE = auto() # Prepare action (find elements, etc)
    ACTION_EXECUTE = auto() # Execute the action
    ACTION_VERIFY = auto()  # Verify action succeeded
    CLEANUP = auto()        # Cleanup resources
    DONE = auto()           # Job completed
    FAILED = auto()         # Job failed


class FailureType(Enum):
    """Failure classification for proper handling"""
    TIMEOUT = "timeout"           # Retry with backoff
    CONDITION_FAIL = "condition"  # Mark state fail, maybe retry
    SYSTEM_CRASH = "crash"        # Restart context
    LOGIC_MISMATCH = "logic"      # Stop job immediately
    NETWORK_ERROR = "network"     # Retry with backoff
    ELEMENT_NOT_FOUND = "element" # Retry or fail


@dataclass
class StateResult:
    """Result from executing a state"""
    success: bool
    next_state: Optional[JobState] = None
    error: Optional[str] = None
    failure_type: Optional[FailureType] = None
    data: Dict = field(default_factory=dict)
    duration_ms: int = 0


@dataclass
class StateConfig:
    """Configuration for a state"""
    timeout_ms: int = 30000
    max_retries: int = 3
    retry_delay_ms: int = 1000
    on_fail: JobState = JobState.FAILED
    entry_condition: Optional[Callable] = None
    exit_condition: Optional[Callable] = None


class StateMachine:
    """
    State Machine for automation jobs
    - Explicit states with clear transitions
    - Entry/exit conditions per state
    - Timeout and retry handling
    - No side-effects between states
    """

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.current_state = JobState.INIT
        self.state_history: List[Dict] = []
        self.state_handlers: Dict[JobState, Callable] = {}
        self.state_configs: Dict[JobState, StateConfig] = {}
        self.context: Dict[str, Any] = {}
        self._lock = threading.Lock()

        # Default configs
        self._setup_default_configs()

    def _setup_default_configs(self):
        """Setup default state configurations"""
        defaults = {
            JobState.INIT: StateConfig(timeout_ms=5000, max_retries=1),
            JobState.OPEN_BROWSER: StateConfig(timeout_ms=60000, max_retries=2),
            JobState.NAVIGATE: StateConfig(timeout_ms=30000, max_retries=3),
            JobState.READY_CHECK: StateConfig(timeout_ms=20000, max_retries=5),
            JobState.ACTION_PREPARE: StateConfig(timeout_ms=15000, max_retries=3),
            JobState.ACTION_EXECUTE: StateConfig(timeout_ms=30000, max_retries=2),
            JobState.ACTION_VERIFY: StateConfig(timeout_ms=15000, max_retries=3),
            JobState.CLEANUP: StateConfig(timeout_ms=10000, max_retries=1),
            JobState.DONE: StateConfig(timeout_ms=1000, max_retries=0),
            JobState.FAILED: StateConfig(timeout_ms=1000, max_retries=0),
        }
        self.state_configs.update(defaults)

    def register_handler(self, state: JobState, handler: Callable[[Dict], StateResult],
                        config: Optional[StateConfig] = None):
        """Register handler for a state"""
        self.state_handlers[state] = handler
        if config:
            self.state_configs[state] = config

    def _record_state(self, state: JobState, result: StateResult):
        """Record state execution to history"""
        self.state_history.append({
            'state': state.name,
            'success': result.success,
            'error': result.error,
            'failure_type': result.failure_type.value if result.failure_type else None,
            'duration_ms': result.duration_ms,
            'timestamp': datetime.now().isoformat(),
            'data': result.data
        })

    def execute_state(self, state: JobState) -> StateResult:
        """Execute a single state with timeout and retry"""
        config = self.state_configs.get(state, StateConfig())
        handler = self.state_handlers.get(state)

        if not handler:
            return StateResult(
                success=False,
                error=f"No handler for state {state.name}",
                failure_type=FailureType.LOGIC_MISMATCH
            )

        # Check entry condition
        if config.entry_condition and not config.entry_condition(self.context):
            return StateResult(
                success=False,
                error=f"Entry condition failed for {state.name}",
                failure_type=FailureType.CONDITION_FAIL
            )

        last_error = None
        for attempt in range(config.max_retries + 1):
            start_time = datetime.now()
            try:
                result = handler(self.context)
                result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                if result.success:
                    # Check exit condition
                    if config.exit_condition and not config.exit_condition(self.context):
                        result = StateResult(
                            success=False,
                            error=f"Exit condition failed for {state.name}",
                            failure_type=FailureType.CONDITION_FAIL,
                            duration_ms=result.duration_ms
                        )
                    else:
                        return result

                last_error = result.error

                # Determine if we should retry based on failure type
                if result.failure_type in [FailureType.LOGIC_MISMATCH, FailureType.SYSTEM_CRASH]:
                    return result  # Don't retry these

                if attempt < config.max_retries:
                    import time
                    time.sleep(config.retry_delay_ms / 1000)

            except Exception as e:
                last_error = str(e)
                duration = int((datetime.now() - start_time).total_seconds() * 1000)

                if attempt >= config.max_retries:
                    return StateResult(
                        success=False,
                        error=f"Exception after {attempt + 1} attempts: {last_error}",
                        failure_type=FailureType.SYSTEM_CRASH,
                        duration_ms=duration
                    )

        return StateResult(
            success=False,
            error=f"Failed after {config.max_retries + 1} attempts: {last_error}",
            failure_type=FailureType.TIMEOUT
        )

    def run(self) -> bool:
        """Run the state machine until DONE or FAILED"""
        # Default state flow
        state_flow = [
            JobState.INIT,
            JobState.OPEN_BROWSER,
            JobState.NAVIGATE,
            JobState.READY_CHECK,
            JobState.ACTION_PREPARE,
            JobState.ACTION_EXECUTE,
            JobState.ACTION_VERIFY,
            JobState.CLEANUP,
            JobState.DONE
        ]

        current_index = 0
        while current_index < len(state_flow):
            state = state_flow[current_index]
            self.current_state = state

            result = self.execute_state(state)
            self._record_state(state, result)

            if not result.success:
                # Execute FAILED state
                self.current_state = JobState.FAILED
                if JobState.FAILED in self.state_handlers:
                    fail_result = self.execute_state(JobState.FAILED)
                    self._record_state(JobState.FAILED, fail_result)
                return False

            # Check for custom next state
            if result.next_state:
                try:
                    current_index = state_flow.index(result.next_state)
                except ValueError:
                    current_index += 1
            else:
                current_index += 1

        return True

    def get_timeline(self) -> List[Dict]:
        """Get execution timeline for debugging"""
        return self.state_history.copy()


class AutomationEngine:
    """
    Main automation engine orchestrating multiple jobs
    - Job queue per context (group/profile)
    - Worker pool with isolation
    - Result tracking
    """

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.jobs: Dict[str, StateMachine] = {}
        self.results: Dict[str, bool] = {}
        self._lock = threading.Lock()
        self._executor = None

    def create_job(self, job_id: str) -> StateMachine:
        """Create a new job state machine"""
        with self._lock:
            sm = StateMachine(job_id)
            self.jobs[job_id] = sm
            return sm

    def run_job(self, job_id: str) -> bool:
        """Run a specific job"""
        sm = self.jobs.get(job_id)
        if not sm:
            return False

        success = sm.run()
        with self._lock:
            self.results[job_id] = success
        return success

    def run_jobs_parallel(self, job_ids: List[str], callback: Callable = None):
        """Run multiple jobs in parallel with isolation"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.run_job, job_id): job_id
                for job_id in job_ids
            }

            for future in as_completed(futures):
                job_id = futures[future]
                try:
                    success = future.result()
                    if callback:
                        callback(job_id, success)
                except Exception as e:
                    if callback:
                        callback(job_id, False, str(e))

    def get_job_timeline(self, job_id: str) -> List[Dict]:
        """Get timeline for a specific job"""
        sm = self.jobs.get(job_id)
        return sm.get_timeline() if sm else []

    def get_all_results(self) -> Dict[str, bool]:
        """Get all job results"""
        with self._lock:
            return self.results.copy()

    def get_statistics(self) -> Dict:
        """Get aggregated statistics"""
        total = len(self.results)
        success = sum(1 for v in self.results.values() if v)
        failed = total - success

        # Aggregate state durations
        state_times = {}
        for job_id, sm in self.jobs.items():
            for entry in sm.get_timeline():
                state = entry['state']
                if state not in state_times:
                    state_times[state] = []
                state_times[state].append(entry['duration_ms'])

        avg_times = {}
        for state, times in state_times.items():
            avg_times[state] = sum(times) / len(times) if times else 0

        return {
            'total_jobs': total,
            'success': success,
            'failed': failed,
            'success_rate': success / total if total > 0 else 0,
            'avg_state_times_ms': avg_times
        }
