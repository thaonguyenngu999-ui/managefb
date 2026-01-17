"""
Job Definitions - Pre-built automation jobs
Each job is isolated and self-contained
Human-like behavior built-in
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import uuid
import traceback

from .engine import StateMachine, JobState, StateResult, FailureType, AutomationEngine
from .cdp_client import CDPClient, Condition, ConditionType
from .artifacts import ArtifactCollector
from .human_behavior import HumanBehavior, AntiDetection


@dataclass
class JobContext:
    """Context passed through all states"""
    job_id: str
    profile_uuid: str
    profile_name: str
    remote_port: Optional[int] = None
    target_url: Optional[str] = None
    action_data: Dict = field(default_factory=dict)
    result_data: Dict = field(default_factory=dict)
    cdp: Optional[CDPClient] = None
    artifacts: Optional[ArtifactCollector] = None


@dataclass
class JobResult:
    """Final result of a job"""
    job_id: str
    success: bool
    error: Optional[str] = None
    duration_ms: int = 0
    timeline: List[Dict] = field(default_factory=list)
    artifact_path: Optional[str] = None
    data: Dict = field(default_factory=dict)


class Job:
    """
    Base job class - isolated execution unit

    Principles:
    - Each job = 1 execution context
    - No shared state between jobs
    - Complete artifact trail
    - Clear success/fail outcome
    """

    def __init__(self, context: JobContext):
        self.context = context
        self.sm = StateMachine(context.job_id)
        self.artifacts = ArtifactCollector()
        self.context.artifacts = self.artifacts
        self._setup_handlers()

    def _setup_handlers(self):
        """Override in subclass to setup state handlers"""
        pass

    def run(self) -> JobResult:
        """Run the job"""
        start = datetime.now()
        self.artifacts.start_job(self.context.job_id, {
            'profile_uuid': self.context.profile_uuid,
            'profile_name': self.context.profile_name,
            'target_url': self.context.target_url,
            'action_data': self.context.action_data
        })

        try:
            success = self.sm.run()

            # Record final state
            final_state = self.sm.current_state.name
            self.artifacts.set_final_state(final_state, success)

            # Get timeline
            timeline = self.sm.get_timeline()

            # Add timeline to artifacts
            for entry in timeline:
                self.artifacts.add_timeline_entry(
                    entry['state'],
                    entry['success'],
                    entry['duration_ms'],
                    entry.get('data')
                )

            # Save artifacts (especially for failed jobs)
            artifact_path = None
            if not success:
                artifact_path = self.artifacts.finish_job(save=True)
            else:
                self.artifacts.finish_job(save=False)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return JobResult(
                job_id=self.context.job_id,
                success=success,
                duration_ms=duration,
                timeline=timeline,
                artifact_path=artifact_path,
                data=self.context.result_data
            )

        except Exception as e:
            self.artifacts.add_error(
                'EXCEPTION',
                str(e),
                self.sm.current_state.name if self.sm else 'UNKNOWN',
                traceback.format_exc()
            )
            artifact_path = self.artifacts.finish_job(save=True)
            duration = int((datetime.now() - start).total_seconds() * 1000)

            return JobResult(
                job_id=self.context.job_id,
                success=False,
                error=str(e),
                duration_ms=duration,
                artifact_path=artifact_path
            )

        finally:
            # Cleanup CDP connection
            if self.context.cdp:
                self.context.cdp.disconnect()


class PostToGroupJob(Job):
    """
    Job: Post content to a Facebook group

    States:
    INIT -> OPEN_BROWSER -> NAVIGATE -> READY_CHECK ->
    ACTION_PREPARE -> ACTION_EXECUTE -> ACTION_VERIFY -> CLEANUP -> DONE
    """

    def _setup_handlers(self):
        """Setup handlers for posting job"""
        self.sm.register_handler(JobState.INIT, self._handle_init)
        self.sm.register_handler(JobState.OPEN_BROWSER, self._handle_open_browser)
        self.sm.register_handler(JobState.NAVIGATE, self._handle_navigate)
        self.sm.register_handler(JobState.READY_CHECK, self._handle_ready_check)
        self.sm.register_handler(JobState.ACTION_PREPARE, self._handle_action_prepare)
        self.sm.register_handler(JobState.ACTION_EXECUTE, self._handle_action_execute)
        self.sm.register_handler(JobState.ACTION_VERIFY, self._handle_action_verify)
        self.sm.register_handler(JobState.CLEANUP, self._handle_cleanup)
        self.sm.register_handler(JobState.DONE, self._handle_done)
        self.sm.register_handler(JobState.FAILED, self._handle_failed)

    def _handle_init(self, ctx: Dict) -> StateResult:
        """Initialize job context"""
        # Validate required data
        if not self.context.target_url:
            return StateResult(
                success=False,
                error="No target URL",
                failure_type=FailureType.LOGIC_MISMATCH
            )

        return StateResult(success=True)

    def _handle_open_browser(self, ctx: Dict) -> StateResult:
        """Open browser via Hidemium API"""
        from api_service import api

        result = api.open_browser(self.context.profile_uuid)

        if result.get('type') == 'error':
            return StateResult(
                success=False,
                error=result.get('message', 'Failed to open browser'),
                failure_type=FailureType.SYSTEM_CRASH
            )

        # Extract port
        data = result.get('data', {})
        remote_port = data.get('remote_port')
        ws_url = data.get('web_socket', '')

        if not remote_port and ws_url:
            import re
            match = re.search(r':(\d+)/', ws_url)
            if match:
                remote_port = int(match.group(1))

        if not remote_port:
            return StateResult(
                success=False,
                error="No remote port in response",
                failure_type=FailureType.SYSTEM_CRASH
            )

        self.context.remote_port = remote_port

        # Create CDP client
        self.context.cdp = CDPClient(remote_port)
        connect_result = self.context.cdp.connect()

        if not connect_result.success:
            return StateResult(
                success=False,
                error=f"CDP connect failed: {connect_result.error}",
                failure_type=FailureType.SYSTEM_CRASH
            )

        return StateResult(success=True, data={'port': remote_port})

    def _handle_navigate(self, ctx: Dict) -> StateResult:
        """Navigate to target URL"""
        cdp = self.context.cdp
        result = cdp.navigate(self.context.target_url)

        if not result.success:
            return StateResult(
                success=False,
                error=f"Navigate failed: {result.error}",
                failure_type=FailureType.NETWORK_ERROR
            )

        return StateResult(success=True)

    def _handle_ready_check(self, ctx: Dict) -> StateResult:
        """Check page is ready for action"""
        cdp = self.context.cdp

        # Wait for page to be fully loaded
        wait_result = cdp.wait_for(
            Condition(ConditionType.PAGE_LOADED, description="Page loaded"),
            timeout_ms=20000
        )

        if not wait_result.success:
            return StateResult(
                success=False,
                error="Page not ready",
                failure_type=FailureType.TIMEOUT
            )

        # Additional check for Facebook group page
        # Look for post creation area
        post_area_result = cdp.wait_for(
            Condition(
                ConditionType.ELEMENT_EXISTS,
                selector='[role="button"][aria-label*="Viết"], [role="button"][aria-label*="Write"]',
                description="Post creation button"
            ),
            timeout_ms=15000
        )

        if not post_area_result.success:
            # Try alternate selector
            post_area_result = cdp.wait_for(
                Condition(
                    ConditionType.ELEMENT_EXISTS,
                    selector='[data-pagelet*="GroupFeed"]',
                    description="Group feed"
                ),
                timeout_ms=10000
            )

        return StateResult(
            success=post_area_result.success,
            error=post_area_result.error if not post_area_result.success else None,
            failure_type=FailureType.CONDITION_FAIL if not post_area_result.success else None
        )

    def _handle_action_prepare(self, ctx: Dict) -> StateResult:
        """Prepare for posting - open post dialog"""
        cdp = self.context.cdp

        # Click on "Write something" or similar button
        click_result = cdp.click(
            '[role="button"][aria-label*="Viết"], '
            '[role="button"][aria-label*="Write"], '
            '[role="textbox"][aria-label*="Viết"]'
        )

        if not click_result.success:
            # Try JavaScript approach
            js = '''
                (function() {
                    let buttons = document.querySelectorAll('[role="button"]');
                    for (let btn of buttons) {
                        let label = btn.getAttribute('aria-label') || '';
                        if (label.includes('Viết') || label.includes('Write')) {
                            btn.click();
                            return true;
                        }
                    }
                    // Try clicking textbox directly
                    let textbox = document.querySelector('[role="textbox"]');
                    if (textbox) {
                        textbox.click();
                        return true;
                    }
                    return false;
                })()
            '''
            result = cdp.execute_js(js)
            if not result.success or not result.data:
                return StateResult(
                    success=False,
                    error="Cannot open post dialog",
                    failure_type=FailureType.ELEMENT_NOT_FOUND
                )

        # Wait for post dialog/textarea to appear (human-like delay)
        HumanBehavior.random_delay(0.8, 1.5)

        return StateResult(success=True)

    def _handle_action_execute(self, ctx: Dict) -> StateResult:
        """Execute the posting action"""
        cdp = self.context.cdp
        content = self.context.action_data.get('content', '')

        if not content:
            return StateResult(
                success=False,
                error="No content to post",
                failure_type=FailureType.LOGIC_MISMATCH
            )

        # Type content into post area
        # Facebook uses contenteditable divs with Lexical editor

        # Step 1: Focus element
        focus_js = '''
            (function() {
                let textbox = document.querySelector('[role="textbox"][contenteditable="true"]');
                if (!textbox) {
                    textbox = document.activeElement;
                }
                if (!textbox || textbox.getAttribute('contenteditable') !== 'true') {
                    return false;
                }

                textbox.focus();
                textbox.innerHTML = '';
                return true;
            })()
        '''

        result = cdp.execute_js(focus_js)
        if not result.success or not result.data:
            return StateResult(
                success=False,
                error="Failed to focus content area",
                failure_type=FailureType.ELEMENT_NOT_FOUND
            )

        # Step 2: Gõ từng ký tự như người thật (hoạt động với Lexical editor)
        try:
            for char in content:
                cdp._send_command('Input.insertText', {'text': char})
                if char in ' .,!?;:\n':
                    time.sleep(random.uniform(0.03, 0.08))
                else:
                    time.sleep(random.uniform(0.015, 0.04))
        except Exception as e:
            print(f"[Jobs] Input.insertText error: {e}")
            return StateResult(
                success=False,
                error=f"Failed to input content: {e}",
                failure_type=FailureType.UNKNOWN
            )

        # Human-like pause after typing before clicking post
        HumanBehavior.think_pause()

        # Click Post button
        post_js = '''
            (function() {
                let buttons = document.querySelectorAll('[role="button"]');
                for (let btn of buttons) {
                    let label = btn.getAttribute('aria-label') || btn.textContent || '';
                    if (label.includes('Đăng') || label.includes('Post') ||
                        label.includes('Xuất bản') || label.includes('Publish')) {
                        if (!btn.disabled && btn.offsetParent !== null) {
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            })()
        '''

        post_result = cdp.execute_js(post_js)
        if not post_result.success or not post_result.data:
            # Take screenshot for debugging
            ss = cdp.take_screenshot()
            if ss.success:
                self.artifacts.add_screenshot('post_button_not_found', ss.data)

            return StateResult(
                success=False,
                error="Post button not found or not clickable",
                failure_type=FailureType.ELEMENT_NOT_FOUND
            )

        return StateResult(success=True)

    def _handle_action_verify(self, ctx: Dict) -> StateResult:
        """Verify post was successful"""
        cdp = self.context.cdp

        # Wait for post to complete (human-like reading time)
        HumanBehavior.random_delay(2.0, 4.0)

        # Check for success indicators:
        # 1. Post dialog closed
        # 2. "Your post has been published" message
        # 3. New post appears in feed

        # Method 1: Check if dialog closed (textbox no longer visible)
        dialog_check = cdp.execute_js('''
            (function() {
                let textbox = document.querySelector('[role="textbox"][contenteditable="true"]');
                if (!textbox) return true; // Dialog closed
                let rect = textbox.getBoundingClientRect();
                return rect.width === 0 || rect.height === 0;
            })()
        ''')

        if dialog_check.success and dialog_check.data:
            self.context.result_data['verified'] = True
            return StateResult(success=True)

        # Method 2: Wait a bit more and check URL for post
        HumanBehavior.random_delay(1.5, 2.5)

        # Take screenshot for manual verification
        ss = cdp.take_screenshot()
        if ss.success:
            self.artifacts.add_screenshot('verification', ss.data)

        # Assume success if no error dialog
        error_check = cdp.execute_js('''
            (function() {
                let errors = document.querySelectorAll('[role="alert"], [role="dialog"] [aria-label*="Error"]');
                return errors.length > 0;
            })()
        ''')

        if error_check.success and error_check.data:
            return StateResult(
                success=False,
                error="Error dialog detected",
                failure_type=FailureType.CONDITION_FAIL
            )

        return StateResult(success=True)

    def _handle_cleanup(self, ctx: Dict) -> StateResult:
        """Cleanup resources"""
        # Close browser if needed
        # (Usually keep open for next job with same profile)
        return StateResult(success=True)

    def _handle_done(self, ctx: Dict) -> StateResult:
        """Job completed successfully"""
        return StateResult(success=True)

    def _handle_failed(self, ctx: Dict) -> StateResult:
        """Handle job failure - capture screenshot"""
        cdp = self.context.cdp
        if cdp:
            ss = cdp.take_screenshot()
            if ss.success:
                self.artifacts.add_screenshot('error', ss.data)

        return StateResult(success=True)  # Failed handler itself succeeded


class LikePostJob(Job):
    """
    Job: Like a Facebook post

    Simpler than posting - just navigate and click like
    """

    def _setup_handlers(self):
        """Setup handlers for like job"""
        self.sm.register_handler(JobState.INIT, self._handle_init)
        self.sm.register_handler(JobState.OPEN_BROWSER, self._handle_open_browser)
        self.sm.register_handler(JobState.NAVIGATE, self._handle_navigate)
        self.sm.register_handler(JobState.READY_CHECK, self._handle_ready_check)
        self.sm.register_handler(JobState.ACTION_PREPARE, self._handle_action_prepare)
        self.sm.register_handler(JobState.ACTION_EXECUTE, self._handle_action_execute)
        self.sm.register_handler(JobState.ACTION_VERIFY, self._handle_action_verify)
        self.sm.register_handler(JobState.CLEANUP, self._handle_cleanup)
        self.sm.register_handler(JobState.DONE, self._handle_done)
        self.sm.register_handler(JobState.FAILED, self._handle_failed)

    def _handle_init(self, ctx: Dict) -> StateResult:
        """Initialize"""
        if not self.context.target_url:
            return StateResult(
                success=False,
                error="No post URL",
                failure_type=FailureType.LOGIC_MISMATCH
            )
        return StateResult(success=True)

    def _handle_open_browser(self, ctx: Dict) -> StateResult:
        """Open browser"""
        from api_service import api

        result = api.open_browser(self.context.profile_uuid)

        if result.get('type') == 'error':
            return StateResult(
                success=False,
                error=result.get('message', 'Failed to open browser'),
                failure_type=FailureType.SYSTEM_CRASH
            )

        data = result.get('data', {})
        remote_port = data.get('remote_port')
        ws_url = data.get('web_socket', '')

        if not remote_port and ws_url:
            import re
            match = re.search(r':(\d+)/', ws_url)
            if match:
                remote_port = int(match.group(1))

        if not remote_port:
            return StateResult(
                success=False,
                error="No remote port",
                failure_type=FailureType.SYSTEM_CRASH
            )

        self.context.remote_port = remote_port
        self.context.cdp = CDPClient(remote_port)
        connect_result = self.context.cdp.connect()

        if not connect_result.success:
            return StateResult(
                success=False,
                error=f"CDP connect failed: {connect_result.error}",
                failure_type=FailureType.SYSTEM_CRASH
            )

        return StateResult(success=True)

    def _handle_navigate(self, ctx: Dict) -> StateResult:
        """Navigate to post"""
        result = self.context.cdp.navigate(self.context.target_url)
        if not result.success:
            return StateResult(
                success=False,
                error=f"Navigate failed: {result.error}",
                failure_type=FailureType.NETWORK_ERROR
            )
        return StateResult(success=True)

    def _handle_ready_check(self, ctx: Dict) -> StateResult:
        """Check post page is ready"""
        cdp = self.context.cdp

        # Wait for like button
        result = cdp.wait_for(
            Condition(
                ConditionType.ELEMENT_EXISTS,
                selector='[aria-label*="Thích"], [aria-label*="Like"]',
                description="Like button"
            ),
            timeout_ms=20000
        )

        return StateResult(
            success=result.success,
            error=result.error if not result.success else None,
            failure_type=FailureType.CONDITION_FAIL if not result.success else None
        )

    def _handle_action_prepare(self, ctx: Dict) -> StateResult:
        """Find the like button"""
        cdp = self.context.cdp

        # Find visible like button in viewport
        js = '''
            (function() {
                let buttons = document.querySelectorAll('[aria-label*="Thích"], [aria-label*="Like"]');
                for (let btn of buttons) {
                    let rect = btn.getBoundingClientRect();
                    if (rect.top > 0 && rect.top < window.innerHeight && rect.width > 0) {
                        return {
                            found: true,
                            y: rect.top,
                            label: btn.getAttribute('aria-label')
                        };
                    }
                }
                return {found: false};
            })()
        '''

        result = cdp.execute_js(js)
        if result.success and result.data and result.data.get('found'):
            self.context.action_data['like_button_found'] = True
            return StateResult(success=True, data=result.data)

        # Scroll down to find it
        cdp.scroll_to(y=300)
        HumanBehavior.random_delay(0.8, 1.2)

        result = cdp.execute_js(js)
        if result.success and result.data and result.data.get('found'):
            self.context.action_data['like_button_found'] = True
            return StateResult(success=True, data=result.data)

        return StateResult(
            success=False,
            error="Like button not found in viewport",
            failure_type=FailureType.ELEMENT_NOT_FOUND
        )

    def _handle_action_execute(self, ctx: Dict) -> StateResult:
        """Click the like button"""
        cdp = self.context.cdp

        js = '''
            (function() {
                let buttons = document.querySelectorAll('[aria-label*="Thích"], [aria-label*="Like"]');
                for (let btn of buttons) {
                    let rect = btn.getBoundingClientRect();
                    if (rect.top > 0 && rect.top < window.innerHeight && rect.width > 0) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            })()
        '''

        result = cdp.execute_js(js)
        if not result.success or not result.data:
            return StateResult(
                success=False,
                error="Click like failed",
                failure_type=FailureType.ELEMENT_NOT_FOUND
            )

        return StateResult(success=True)

    def _handle_action_verify(self, ctx: Dict) -> StateResult:
        """Verify like was successful"""
        cdp = self.context.cdp
        # Human-like wait after clicking
        HumanBehavior.random_delay(0.8, 1.5)

        # Check if button changed (label should change to "Bỏ thích" / "Unlike")
        js = '''
            (function() {
                let unlikeBtn = document.querySelector('[aria-label*="Bỏ thích"], [aria-label*="Unlike"]');
                return unlikeBtn !== null;
            })()
        '''

        result = cdp.execute_js(js)
        if result.success and result.data:
            self.context.result_data['liked'] = True
            return StateResult(success=True)

        # May already have been liked, still success
        return StateResult(success=True)

    def _handle_cleanup(self, ctx: Dict) -> StateResult:
        return StateResult(success=True)

    def _handle_done(self, ctx: Dict) -> StateResult:
        return StateResult(success=True)

    def _handle_failed(self, ctx: Dict) -> StateResult:
        if self.context.cdp:
            ss = self.context.cdp.take_screenshot()
            if ss.success:
                self.artifacts.add_screenshot('error', ss.data)
        return StateResult(success=True)


# ============================================================
# CDP MAX JOBS - Using production-grade CDP implementation
# ============================================================

from .cdp_max import CDPClientMAX, CDPClientConfig, Locator, Postcondition
from .cdp_max.observability import ReasonCode


@dataclass
class JobContextMAX:
    """Context for MAX jobs with CDPClientMAX"""
    job_id: str
    profile_uuid: str
    profile_name: str
    remote_port: Optional[int] = None
    target_url: Optional[str] = None
    action_data: Dict = field(default_factory=dict)
    result_data: Dict = field(default_factory=dict)
    cdp: Optional[CDPClientMAX] = None
    artifacts: Optional[ArtifactCollector] = None


class JobMAX:
    """
    Base job class using CDPClientMAX

    Features from CDP MAX:
    - Auto-reconnect if connection drops
    - Heartbeat health check
    - Backpressure control
    - Locator-based element selection
    - Pre/postcondition verification
    - Recovery system
    """

    def __init__(self, context: JobContextMAX):
        self.context = context
        self.sm = StateMachine(context.job_id)
        self.artifacts = ArtifactCollector()
        self.context.artifacts = self.artifacts
        self._setup_handlers()

    def _setup_handlers(self):
        """Override in subclass"""
        pass

    def run(self) -> JobResult:
        """Run the job with CDP MAX"""
        start = datetime.now()
        self.artifacts.start_job(self.context.job_id, {
            'profile_uuid': self.context.profile_uuid,
            'profile_name': self.context.profile_name,
            'target_url': self.context.target_url,
            'action_data': self.context.action_data
        })

        try:
            # Start job tracking in CDP
            if self.context.cdp:
                self.context.cdp.start_job(
                    self.context.job_id,
                    self.__class__.__name__,
                    {'profile': self.context.profile_name}
                )

            success = self.sm.run()

            # End job tracking
            if self.context.cdp:
                self.context.cdp.end_job(success)

            # Record final state
            final_state = self.sm.current_state.name
            self.artifacts.set_final_state(final_state, success)

            timeline = self.sm.get_timeline()
            for entry in timeline:
                self.artifacts.add_timeline_entry(
                    entry['state'],
                    entry['success'],
                    entry['duration_ms'],
                    entry.get('data')
                )

            artifact_path = None
            if not success:
                artifact_path = self.artifacts.finish_job(save=True)
            else:
                self.artifacts.finish_job(save=False)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return JobResult(
                job_id=self.context.job_id,
                success=success,
                duration_ms=duration,
                timeline=timeline,
                artifact_path=artifact_path,
                data=self.context.result_data
            )

        except Exception as e:
            self.artifacts.add_error(
                'EXCEPTION',
                str(e),
                self.sm.current_state.name if self.sm else 'UNKNOWN',
                traceback.format_exc()
            )
            artifact_path = self.artifacts.finish_job(save=True)
            duration = int((datetime.now() - start).total_seconds() * 1000)

            return JobResult(
                job_id=self.context.job_id,
                success=False,
                error=str(e),
                duration_ms=duration,
                artifact_path=artifact_path
            )

        finally:
            if self.context.cdp:
                self.context.cdp.close()


class PostToGroupJobMAX(JobMAX):
    """
    Post to Facebook group using CDP MAX

    Uses:
    - Locator-based element selection (by_role, by_aria_label)
    - Postcondition verification
    - Human-like delays
    - Recovery on failure
    """

    def _setup_handlers(self):
        self.sm.register_handler(JobState.INIT, self._handle_init)
        self.sm.register_handler(JobState.OPEN_BROWSER, self._handle_open_browser)
        self.sm.register_handler(JobState.NAVIGATE, self._handle_navigate)
        self.sm.register_handler(JobState.READY_CHECK, self._handle_ready_check)
        self.sm.register_handler(JobState.ACTION_PREPARE, self._handle_action_prepare)
        self.sm.register_handler(JobState.ACTION_EXECUTE, self._handle_action_execute)
        self.sm.register_handler(JobState.ACTION_VERIFY, self._handle_action_verify)
        self.sm.register_handler(JobState.CLEANUP, self._handle_cleanup)
        self.sm.register_handler(JobState.DONE, self._handle_done)
        self.sm.register_handler(JobState.FAILED, self._handle_failed)

    def _handle_init(self, ctx: Dict) -> StateResult:
        if not self.context.target_url:
            return StateResult(
                success=False,
                error="No target URL",
                failure_type=FailureType.LOGIC_MISMATCH
            )
        return StateResult(success=True)

    def _handle_open_browser(self, ctx: Dict) -> StateResult:
        from api_service import api

        result = api.open_browser(self.context.profile_uuid)

        if result.get('type') == 'error':
            return StateResult(
                success=False,
                error=result.get('message', 'Failed to open browser'),
                failure_type=FailureType.SYSTEM_CRASH
            )

        data = result.get('data', {})
        remote_port = data.get('remote_port')
        ws_url = data.get('web_socket', '')

        if not remote_port and ws_url:
            import re
            match = re.search(r':(\d+)/', ws_url)
            if match:
                remote_port = int(match.group(1))

        if not remote_port:
            return StateResult(
                success=False,
                error="No remote port in response",
                failure_type=FailureType.SYSTEM_CRASH
            )

        self.context.remote_port = remote_port

        # Create CDP MAX client
        config = CDPClientConfig(
            remote_port=remote_port,
            auto_reconnect=True,
            enable_watchdog=True,
            enable_recovery=True
        )
        self.context.cdp = CDPClientMAX(config)
        success, reason = self.context.cdp.connect()

        if not success:
            return StateResult(
                success=False,
                error=f"CDP connect failed: {reason.message if reason else 'unknown'}",
                failure_type=FailureType.SYSTEM_CRASH
            )

        return StateResult(success=True, data={'port': remote_port})

    def _handle_navigate(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp
        result = cdp.navigate(self.context.target_url, wait_until='load')

        if not result.success:
            return StateResult(
                success=False,
                error=f"Navigate failed: {result.error}",
                failure_type=FailureType.NETWORK_ERROR
            )

        # Human-like pause after navigation
        HumanBehavior.random_delay(1.0, 2.0)

        return StateResult(success=True)

    def _handle_ready_check(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp

        # Wait for page loaded
        wait_result = cdp.wait_for_network_idle(timeout_ms=15000)

        # Check for post creation area using locators
        # Try Vietnamese first, then English
        write_button = cdp.by_aria_label("Viết")
        if not cdp.exists(write_button):
            write_button = cdp.by_aria_label("Write")

        if not cdp.exists(write_button):
            # Try generic textbox
            textbox = cdp.by_role("textbox")
            if not cdp.exists(textbox):
                return StateResult(
                    success=False,
                    error="Post creation area not found",
                    failure_type=FailureType.CONDITION_FAIL
                )

        return StateResult(success=True)

    def _handle_action_prepare(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp

        # Click on write button/textbox to open post dialog
        # Try different selectors
        selectors_to_try = [
            cdp.by_aria_label("Viết"),
            cdp.by_aria_label("Write"),
            cdp.by_role("textbox"),
        ]

        clicked = False
        for locator in selectors_to_try:
            if cdp.exists(locator):
                result = cdp.click(locator)
                if result.success:
                    clicked = True
                    break

        if not clicked:
            # Fallback to JS click
            js = '''
                (function() {
                    let textbox = document.querySelector('[role="textbox"]');
                    if (textbox) {
                        textbox.click();
                        return true;
                    }
                    return false;
                })()
            '''
            if not cdp.execute(js):
                return StateResult(
                    success=False,
                    error="Cannot open post dialog",
                    failure_type=FailureType.ELEMENT_NOT_FOUND
                )

        # Human-like wait for dialog
        HumanBehavior.random_delay(0.8, 1.5)

        return StateResult(success=True)

    def _handle_action_execute(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp
        content = self.context.action_data.get('content', '')

        if not content:
            return StateResult(
                success=False,
                error="No content to post",
                failure_type=FailureType.LOGIC_MISMATCH
            )

        # Type content - Facebook uses Lexical editor với contenteditable

        # Step 1: Focus element
        focus_js = '''
            (function() {
                let textbox = document.querySelector('[role="textbox"][contenteditable="true"]');
                if (!textbox) textbox = document.activeElement;
                if (!textbox || textbox.getAttribute('contenteditable') !== 'true') return false;

                textbox.focus();
                textbox.innerHTML = '';
                return true;
            })()
        '''

        if not cdp.execute(focus_js):
            return StateResult(
                success=False,
                error="Failed to focus content area",
                failure_type=FailureType.ELEMENT_NOT_FOUND
            )

        # Step 2: Gõ từng ký tự như người thật (hoạt động với Lexical editor)
        try:
            for char in content:
                cdp.session.send_command('Input.insertText', {'text': char})
                if char in ' .,!?;:\n':
                    time.sleep(random.uniform(0.03, 0.08))
                else:
                    time.sleep(random.uniform(0.015, 0.04))
        except Exception as e:
            print(f"[Jobs] Input.insertText error: {e}")
            return StateResult(
                success=False,
                error=f"Failed to input content: {e}",
                failure_type=FailureType.UNKNOWN
            )

        # Human-like think pause
        HumanBehavior.think_pause()

        # Click Post button
        post_locators = [
            cdp.by_aria_label("Đăng"),
            cdp.by_aria_label("Post"),
            cdp.by_text("Đăng"),
            cdp.by_text("Post"),
        ]

        clicked = False
        for locator in post_locators:
            if cdp.exists(locator):
                # Define postcondition: dialog should close
                postcond = Postcondition(
                    check=lambda: not cdp.exists(cdp.by_css('[role="textbox"][contenteditable="true"]')),
                    description="Post dialog closed",
                    timeout_ms=10000
                )
                result = cdp.click(locator, postcondition=postcond)
                if result.success:
                    clicked = True
                    break

        if not clicked:
            # Fallback to JS
            post_js = '''
                (function() {
                    let buttons = document.querySelectorAll('[role="button"]');
                    for (let btn of buttons) {
                        let label = btn.getAttribute('aria-label') || btn.textContent || '';
                        if (label.includes('Đăng') || label.includes('Post')) {
                            if (!btn.disabled && btn.offsetParent !== null) {
                                btn.click();
                                return true;
                            }
                        }
                    }
                    return false;
                })()
            '''
            if not cdp.execute(post_js):
                # Take screenshot for debugging
                ss = cdp.take_screenshot(reason='post_button_not_found')
                if ss:
                    self.artifacts.add_screenshot('post_button_not_found', ss)
                return StateResult(
                    success=False,
                    error="Post button not found",
                    failure_type=FailureType.ELEMENT_NOT_FOUND
                )

        return StateResult(success=True)

    def _handle_action_verify(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp

        # Wait for post completion
        HumanBehavior.random_delay(2.0, 4.0)

        # Check if dialog closed (success indicator)
        textbox = cdp.by_css('[role="textbox"][contenteditable="true"]')
        if not cdp.exists(textbox):
            self.context.result_data['verified'] = True
            return StateResult(success=True)

        # Take screenshot for verification
        ss = cdp.take_screenshot(reason='verification')
        if ss:
            self.artifacts.add_screenshot('verification', ss)

        # Check for error dialog
        error_check = cdp.evaluate('[role="alert"]') is not None
        if error_check:
            return StateResult(
                success=False,
                error="Error dialog detected",
                failure_type=FailureType.CONDITION_FAIL
            )

        return StateResult(success=True)

    def _handle_cleanup(self, ctx: Dict) -> StateResult:
        return StateResult(success=True)

    def _handle_done(self, ctx: Dict) -> StateResult:
        return StateResult(success=True)

    def _handle_failed(self, ctx: Dict) -> StateResult:
        if self.context.cdp:
            ss = self.context.cdp.take_screenshot(reason='error')
            if ss:
                self.artifacts.add_screenshot('error', ss)
        return StateResult(success=True)


class LikePostJobMAX(JobMAX):
    """
    Like a Facebook post using CDP MAX

    Uses semantic locators and postcondition verification
    """

    def _setup_handlers(self):
        self.sm.register_handler(JobState.INIT, self._handle_init)
        self.sm.register_handler(JobState.OPEN_BROWSER, self._handle_open_browser)
        self.sm.register_handler(JobState.NAVIGATE, self._handle_navigate)
        self.sm.register_handler(JobState.READY_CHECK, self._handle_ready_check)
        self.sm.register_handler(JobState.ACTION_PREPARE, self._handle_action_prepare)
        self.sm.register_handler(JobState.ACTION_EXECUTE, self._handle_action_execute)
        self.sm.register_handler(JobState.ACTION_VERIFY, self._handle_action_verify)
        self.sm.register_handler(JobState.CLEANUP, self._handle_cleanup)
        self.sm.register_handler(JobState.DONE, self._handle_done)
        self.sm.register_handler(JobState.FAILED, self._handle_failed)

    def _handle_init(self, ctx: Dict) -> StateResult:
        if not self.context.target_url:
            return StateResult(
                success=False,
                error="No post URL",
                failure_type=FailureType.LOGIC_MISMATCH
            )
        return StateResult(success=True)

    def _handle_open_browser(self, ctx: Dict) -> StateResult:
        from api_service import api

        result = api.open_browser(self.context.profile_uuid)

        if result.get('type') == 'error':
            return StateResult(
                success=False,
                error=result.get('message', 'Failed to open browser'),
                failure_type=FailureType.SYSTEM_CRASH
            )

        data = result.get('data', {})
        remote_port = data.get('remote_port')
        ws_url = data.get('web_socket', '')

        if not remote_port and ws_url:
            import re
            match = re.search(r':(\d+)/', ws_url)
            if match:
                remote_port = int(match.group(1))

        if not remote_port:
            return StateResult(
                success=False,
                error="No remote port",
                failure_type=FailureType.SYSTEM_CRASH
            )

        self.context.remote_port = remote_port

        config = CDPClientConfig(
            remote_port=remote_port,
            auto_reconnect=True,
            enable_recovery=True
        )
        self.context.cdp = CDPClientMAX(config)
        success, reason = self.context.cdp.connect()

        if not success:
            return StateResult(
                success=False,
                error=f"CDP connect failed: {reason.message if reason else 'unknown'}",
                failure_type=FailureType.SYSTEM_CRASH
            )

        return StateResult(success=True)

    def _handle_navigate(self, ctx: Dict) -> StateResult:
        result = self.context.cdp.navigate(self.context.target_url)
        if not result.success:
            return StateResult(
                success=False,
                error=f"Navigate failed: {result.error}",
                failure_type=FailureType.NETWORK_ERROR
            )
        HumanBehavior.random_delay(1.0, 2.0)
        return StateResult(success=True)

    def _handle_ready_check(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp

        # Wait for like button using semantic locator
        like_button_vn = cdp.by_aria_label("Thích")
        like_button_en = cdp.by_aria_label("Like")

        cdp.wait_for_network_idle(timeout_ms=10000)

        if cdp.exists(like_button_vn) or cdp.exists(like_button_en):
            return StateResult(success=True)

        return StateResult(
            success=False,
            error="Like button not found",
            failure_type=FailureType.CONDITION_FAIL
        )

    def _handle_action_prepare(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp

        # Find visible like button
        like_vn = cdp.by_aria_label("Thích")
        like_en = cdp.by_aria_label("Like")

        if cdp.is_visible(like_vn):
            self.context.action_data['like_locator'] = like_vn
            return StateResult(success=True)
        elif cdp.is_visible(like_en):
            self.context.action_data['like_locator'] = like_en
            return StateResult(success=True)

        # Scroll to find it
        cdp.execute('window.scrollBy(0, 300)')
        HumanBehavior.random_delay(0.5, 1.0)

        if cdp.is_visible(like_vn):
            self.context.action_data['like_locator'] = like_vn
            return StateResult(success=True)
        elif cdp.is_visible(like_en):
            self.context.action_data['like_locator'] = like_en
            return StateResult(success=True)

        return StateResult(
            success=False,
            error="Like button not visible",
            failure_type=FailureType.ELEMENT_NOT_FOUND
        )

    def _handle_action_execute(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp
        locator = self.context.action_data.get('like_locator')

        if locator:
            # Define postcondition: button should change to "Unlike"
            def check_liked():
                unlike_vn = cdp.by_aria_label("Bỏ thích")
                unlike_en = cdp.by_aria_label("Unlike")
                return cdp.exists(unlike_vn) or cdp.exists(unlike_en)

            postcond = Postcondition(
                check=check_liked,
                description="Like button changed to Unlike",
                timeout_ms=5000
            )

            result = cdp.click(locator, postcondition=postcond)
            if result.success:
                return StateResult(success=True)

        # Fallback to JS
        js = '''
            (function() {
                let buttons = document.querySelectorAll('[aria-label*="Thích"], [aria-label*="Like"]');
                for (let btn of buttons) {
                    let rect = btn.getBoundingClientRect();
                    if (rect.top > 0 && rect.top < window.innerHeight && rect.width > 0) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            })()
        '''

        if not cdp.execute(js):
            return StateResult(
                success=False,
                error="Click like failed",
                failure_type=FailureType.ELEMENT_NOT_FOUND
            )

        return StateResult(success=True)

    def _handle_action_verify(self, ctx: Dict) -> StateResult:
        cdp = self.context.cdp
        HumanBehavior.random_delay(0.8, 1.5)

        # Check for Unlike button (indicates success)
        unlike_vn = cdp.by_aria_label("Bỏ thích")
        unlike_en = cdp.by_aria_label("Unlike")

        if cdp.exists(unlike_vn) or cdp.exists(unlike_en):
            self.context.result_data['liked'] = True
            return StateResult(success=True)

        # May already have been liked
        return StateResult(success=True)

    def _handle_cleanup(self, ctx: Dict) -> StateResult:
        return StateResult(success=True)

    def _handle_done(self, ctx: Dict) -> StateResult:
        return StateResult(success=True)

    def _handle_failed(self, ctx: Dict) -> StateResult:
        if self.context.cdp:
            ss = self.context.cdp.take_screenshot(reason='error')
            if ss:
                self.artifacts.add_screenshot('error', ss)
        return StateResult(success=True)
