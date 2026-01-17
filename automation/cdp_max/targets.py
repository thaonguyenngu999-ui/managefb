"""
Target Management MAX - Multi-tab/target handling

Features:
- Track all browser targets (tabs, popups, service workers)
- Automatic target attachment
- No "lost tab" when site opens popup/new tab
- Target lifecycle management
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import threading
import time

from .events import EventEmitter, CDPEvent, EventType
from .session import CDPSession, CommandResult


class TargetType(Enum):
    """Browser target types"""
    PAGE = "page"
    IFRAME = "iframe"
    BACKGROUND_PAGE = "background_page"
    SERVICE_WORKER = "service_worker"
    SHARED_WORKER = "shared_worker"
    BROWSER = "browser"
    WEBVIEW = "webview"
    OTHER = "other"


@dataclass
class Target:
    """A browser target (tab, iframe, worker, etc.)"""
    target_id: str
    type: TargetType
    url: str
    title: str = ""
    attached: bool = False
    session_id: Optional[str] = None
    opener_id: Optional[str] = None
    browser_context_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_url: str = ""
    is_main: bool = False

    @classmethod
    def from_target_info(cls, info: Dict) -> 'Target':
        """Create Target from CDP Target.targetInfo"""
        target_type = info.get('type', 'other')
        try:
            ttype = TargetType(target_type)
        except ValueError:
            ttype = TargetType.OTHER

        return cls(
            target_id=info.get('targetId', ''),
            type=ttype,
            url=info.get('url', ''),
            title=info.get('title', ''),
            attached=info.get('attached', False),
            opener_id=info.get('openerId'),
            browser_context_id=info.get('browserContextId')
        )


class TargetManager:
    """
    Manages all browser targets

    Responsibilities:
    - Track target creation/destruction
    - Auto-attach to new targets
    - Provide target lookup
    - Handle popups and new tabs
    """

    def __init__(self, session: CDPSession, auto_attach: bool = True):
        self._session = session
        self._auto_attach = auto_attach
        self._targets: Dict[str, Target] = {}
        self._main_target_id: Optional[str] = None
        self._lock = threading.Lock()

        # Callbacks
        self._on_target_created: List[Callable[[Target], None]] = []
        self._on_target_destroyed: List[Callable[[str], None]] = []
        self._on_target_changed: List[Callable[[Target], None]] = []

        # Subscribe to target events
        self._session.events.on(EventType.TARGET_CREATED, self._handle_target_created)
        self._session.events.on(EventType.TARGET_DESTROYED, self._handle_target_destroyed)
        self._session.events.on(EventType.TARGET_INFO_CHANGED, self._handle_target_changed)
        self._session.events.on(EventType.TARGET_CRASHED, self._handle_target_crashed)

    def initialize(self) -> bool:
        """Initialize target tracking"""
        # Enable target discovery
        result = self._session.send_command('Target.setDiscoverTargets', {
            'discover': True
        })

        if not result.success:
            return False

        # Get existing targets
        result = self._session.send_command('Target.getTargets')
        if result.success and result.result:
            target_infos = result.result.get('targetInfos', [])
            for info in target_infos:
                target = Target.from_target_info(info)
                with self._lock:
                    self._targets[target.target_id] = target

                # Set first page as main target
                if target.type == TargetType.PAGE and not self._main_target_id:
                    self._main_target_id = target.target_id
                    target.is_main = True

        # Auto-attach if enabled
        if self._auto_attach:
            self._session.send_command('Target.setAutoAttach', {
                'autoAttach': True,
                'waitForDebuggerOnStart': False,
                'flatten': True
            })

        return True

    def _handle_target_created(self, event: CDPEvent):
        """Handle new target creation"""
        target_info = event.data.get('targetInfo', {})
        target = Target.from_target_info(target_info)

        with self._lock:
            self._targets[target.target_id] = target

        # Auto-attach to pages
        if self._auto_attach and target.type == TargetType.PAGE:
            self.attach_to_target(target.target_id)

        # Notify callbacks
        for callback in self._on_target_created:
            try:
                callback(target)
            except:
                pass

    def _handle_target_destroyed(self, event: CDPEvent):
        """Handle target destruction"""
        target_id = event.data.get('targetId')

        with self._lock:
            self._targets.pop(target_id, None)
            if self._main_target_id == target_id:
                # Find new main target
                for tid, t in self._targets.items():
                    if t.type == TargetType.PAGE:
                        self._main_target_id = tid
                        t.is_main = True
                        break

        # Notify callbacks
        for callback in self._on_target_destroyed:
            try:
                callback(target_id)
            except:
                pass

    def _handle_target_changed(self, event: CDPEvent):
        """Handle target info change"""
        target_info = event.data.get('targetInfo', {})
        target_id = target_info.get('targetId')

        with self._lock:
            if target_id in self._targets:
                target = self._targets[target_id]
                target.url = target_info.get('url', target.url)
                target.title = target_info.get('title', target.title)
                target.last_url = target.url

        # Notify callbacks
        target = self._targets.get(target_id)
        if target:
            for callback in self._on_target_changed:
                try:
                    callback(target)
                except:
                    pass

    def _handle_target_crashed(self, event: CDPEvent):
        """Handle target crash"""
        target_id = event.data.get('targetId')

        with self._lock:
            if target_id in self._targets:
                # Mark as crashed but don't remove
                self._targets[target_id].attached = False

    def attach_to_target(self, target_id: str) -> Optional[str]:
        """Attach to a target and return session ID"""
        result = self._session.send_command('Target.attachToTarget', {
            'targetId': target_id,
            'flatten': True
        })

        if result.success and result.result:
            session_id = result.result.get('sessionId')
            with self._lock:
                if target_id in self._targets:
                    self._targets[target_id].attached = True
                    self._targets[target_id].session_id = session_id
            return session_id

        return None

    def detach_from_target(self, session_id: str) -> bool:
        """Detach from a target"""
        result = self._session.send_command('Target.detachFromTarget', {
            'sessionId': session_id
        })

        if result.success:
            with self._lock:
                for target in self._targets.values():
                    if target.session_id == session_id:
                        target.attached = False
                        target.session_id = None
                        break

        return result.success

    def get_target(self, target_id: str) -> Optional[Target]:
        """Get target by ID"""
        with self._lock:
            return self._targets.get(target_id)

    def get_main_target(self) -> Optional[Target]:
        """Get main page target"""
        with self._lock:
            if self._main_target_id:
                return self._targets.get(self._main_target_id)
        return None

    def get_all_targets(self, target_type: TargetType = None) -> List[Target]:
        """Get all targets, optionally filtered by type"""
        with self._lock:
            if target_type:
                return [t for t in self._targets.values() if t.type == target_type]
            return list(self._targets.values())

    def get_pages(self) -> List[Target]:
        """Get all page targets"""
        return self.get_all_targets(TargetType.PAGE)

    def find_target_by_url(self, url_pattern: str) -> Optional[Target]:
        """Find target by URL pattern"""
        with self._lock:
            for target in self._targets.values():
                if url_pattern in target.url:
                    return target
        return None

    def wait_for_target(self, url_pattern: str = None, target_type: TargetType = None,
                       timeout_ms: int = 30000) -> Optional[Target]:
        """Wait for a target matching criteria"""
        deadline = datetime.now().timestamp() + (timeout_ms / 1000)

        while datetime.now().timestamp() < deadline:
            with self._lock:
                for target in self._targets.values():
                    if target_type and target.type != target_type:
                        continue
                    if url_pattern and url_pattern not in target.url:
                        continue
                    return target

            time.sleep(0.1)

        return None

    def wait_for_popup(self, timeout_ms: int = 30000) -> Optional[Target]:
        """Wait for a popup window"""
        initial_targets = set(self._targets.keys())

        deadline = datetime.now().timestamp() + (timeout_ms / 1000)

        while datetime.now().timestamp() < deadline:
            with self._lock:
                for target_id, target in self._targets.items():
                    if target_id not in initial_targets and target.type == TargetType.PAGE:
                        return target

            time.sleep(0.1)

        return None

    def close_target(self, target_id: str) -> bool:
        """Close a target"""
        result = self._session.send_command('Target.closeTarget', {
            'targetId': target_id
        })
        return result.success

    def create_target(self, url: str) -> Optional[Target]:
        """Create a new page target"""
        result = self._session.send_command('Target.createTarget', {
            'url': url
        })

        if result.success and result.result:
            target_id = result.result.get('targetId')
            # Wait for target to appear
            return self.wait_for_target(timeout_ms=5000)

        return None

    def set_main_target(self, target_id: str):
        """Set the main target"""
        with self._lock:
            if target_id in self._targets:
                # Unset old main
                if self._main_target_id and self._main_target_id in self._targets:
                    self._targets[self._main_target_id].is_main = False
                # Set new main
                self._main_target_id = target_id
                self._targets[target_id].is_main = True

    def on_target_created(self, callback: Callable[[Target], None]):
        """Register callback for target creation"""
        self._on_target_created.append(callback)

    def on_target_destroyed(self, callback: Callable[[str], None]):
        """Register callback for target destruction"""
        self._on_target_destroyed.append(callback)

    def on_target_changed(self, callback: Callable[[Target], None]):
        """Register callback for target changes"""
        self._on_target_changed.append(callback)

    def get_status(self) -> Dict:
        """Get target manager status"""
        with self._lock:
            return {
                'total_targets': len(self._targets),
                'pages': len([t for t in self._targets.values() if t.type == TargetType.PAGE]),
                'attached': len([t for t in self._targets.values() if t.attached]),
                'main_target_id': self._main_target_id,
                'targets': [
                    {
                        'id': t.target_id,
                        'type': t.type.value,
                        'url': t.url[:100],
                        'attached': t.attached,
                        'is_main': t.is_main
                    }
                    for t in self._targets.values()
                ]
            }
