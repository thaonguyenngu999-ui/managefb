"""
File I/O MAX - Upload/Download handling

Upload:
- Confirm input received file
- Confirm preview/render completed before submit

Download:
- Catch download event
- Check file exists + size stable
- Checksum (if needed)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import os
import time
import hashlib

from .session import CDPSession, CommandResult
from .events import EventEmitter, CDPEvent, EventType
from .waits import WaitEngine, WaitCondition, ConditionType
from .selectors import SelectorEngine, Locator
from .observability import ReasonCode, FailureReason


@dataclass
class UploadResult:
    """Result from file upload"""
    success: bool
    file_path: str
    elapsed_ms: int
    error: Optional[str] = None
    reason: Optional[FailureReason] = None
    preview_verified: bool = False
    file_size: int = 0


@dataclass
class DownloadResult:
    """Result from file download"""
    success: bool
    download_path: Optional[str]
    elapsed_ms: int
    error: Optional[str] = None
    reason: Optional[FailureReason] = None
    file_size: int = 0
    checksum: Optional[str] = None


class FileIOManager:
    """
    Manages file uploads and downloads

    Upload flow:
    1. Find file input
    2. Set files via CDP
    3. Wait for preview/processing
    4. Verify upload state

    Download flow:
    1. Intercept download request
    2. Track download progress
    3. Verify file exists and size stable
    """

    def __init__(self, session: CDPSession, waits: WaitEngine,
                 download_dir: str = None):
        self._session = session
        self._waits = waits
        self._download_dir = download_dir or os.path.join(os.path.expanduser('~'), 'Downloads')

        # Download tracking
        self._pending_downloads: Dict[str, Dict] = {}
        self._completed_downloads: Dict[str, Dict] = {}

        # Subscribe to download events
        session.events.on(EventType.BROWSER_DOWNLOAD_WILL_BEGIN, self._on_download_begin)
        session.events.on(EventType.BROWSER_DOWNLOAD_PROGRESS, self._on_download_progress)

    def _on_download_begin(self, event: CDPEvent):
        """Track download start"""
        guid = event.data.get('guid', '')
        self._pending_downloads[guid] = {
            'url': event.data.get('url', ''),
            'suggested_filename': event.data.get('suggestedFilename', ''),
            'started_at': datetime.now().isoformat(),
            'state': 'started'
        }

    def _on_download_progress(self, event: CDPEvent):
        """Track download progress"""
        guid = event.data.get('guid', '')
        state = event.data.get('state', '')

        if guid in self._pending_downloads:
            self._pending_downloads[guid]['state'] = state
            self._pending_downloads[guid]['received_bytes'] = event.data.get('receivedBytes', 0)
            self._pending_downloads[guid]['total_bytes'] = event.data.get('totalBytes', 0)

            if state == 'completed':
                self._completed_downloads[guid] = self._pending_downloads.pop(guid)
                self._completed_downloads[guid]['completed_at'] = datetime.now().isoformat()

    def upload_file(self, file_input_selector: str, file_path: str,
                    verify_preview: bool = True, timeout_ms: int = 30000) -> UploadResult:
        """
        Upload a file to file input

        Args:
            file_input_selector: CSS selector for file input
            file_path: Path to file to upload
            verify_preview: Whether to verify preview loaded
            timeout_ms: Maximum wait time
        """
        start_time = datetime.now()

        # Verify file exists
        if not os.path.exists(file_path):
            return UploadResult(
                success=False,
                file_path=file_path,
                elapsed_ms=0,
                error=f"File not found: {file_path}",
                reason=FailureReason(
                    code=ReasonCode.UPLOAD_FAILED,
                    message=f"File not found: {file_path}"
                )
            )

        file_size = os.path.getsize(file_path)

        # Find file input element
        wait_result = self._waits.wait_for(
            WaitCondition(type=ConditionType.ELEMENT_EXISTS, selector=file_input_selector),
            timeout_ms=10000
        )

        if not wait_result.success:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return UploadResult(
                success=False,
                file_path=file_path,
                elapsed_ms=elapsed,
                error="File input not found",
                reason=FailureReason(
                    code=ReasonCode.ELEMENT_NOT_FOUND,
                    message=f"File input not found: {file_input_selector}"
                )
            )

        # Get DOM node ID for file input
        selector_escaped = file_input_selector.replace("'", "\\'")
        js = f"""
            (function() {{
                let input = document.querySelector('{selector_escaped}');
                return input ? true : false;
            }})()
        """

        result = self._session.evaluate_js(js)
        if not result.success or not result.result.get('result', {}).get('value'):
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return UploadResult(
                success=False,
                file_path=file_path,
                elapsed_ms=elapsed,
                error="File input element not accessible",
                reason=FailureReason(
                    code=ReasonCode.ELEMENT_NOT_FOUND,
                    message="Could not access file input"
                )
            )

        # Get document and find input node
        doc_result = self._session.send_command('DOM.getDocument')
        if not doc_result.success:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return UploadResult(
                success=False,
                file_path=file_path,
                elapsed_ms=elapsed,
                error="Could not get document"
            )

        doc_node_id = doc_result.result.get('root', {}).get('nodeId')

        query_result = self._session.send_command('DOM.querySelector', {
            'nodeId': doc_node_id,
            'selector': file_input_selector
        })

        if not query_result.success or not query_result.result.get('nodeId'):
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return UploadResult(
                success=False,
                file_path=file_path,
                elapsed_ms=elapsed,
                error="File input node not found"
            )

        node_id = query_result.result.get('nodeId')

        # Set files on the input
        set_result = self._session.send_command('DOM.setFileInputFiles', {
            'nodeId': node_id,
            'files': [file_path]
        })

        if not set_result.success:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return UploadResult(
                success=False,
                file_path=file_path,
                elapsed_ms=elapsed,
                error=f"Failed to set file: {set_result.error}",
                reason=FailureReason(
                    code=ReasonCode.UPLOAD_FAILED,
                    message=set_result.error or "Failed to set file"
                )
            )

        # Trigger change event
        js_trigger = f"""
            (function() {{
                let input = document.querySelector('{selector_escaped}');
                if (input) {{
                    input.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return true;
                }}
                return false;
            }})()
        """
        self._session.evaluate_js(js_trigger)

        # Verify preview if requested
        preview_verified = False
        if verify_preview:
            # Wait for preview/thumbnail to appear
            # Common patterns for file previews
            preview_selectors = [
                'img[src*="blob:"]',  # Blob URLs for previews
                'img[src*="data:"]',  # Data URLs
                '.preview',
                '.thumbnail',
                '[data-preview]',
                '.file-preview',
                '.upload-preview'
            ]

            remaining = timeout_ms - int((datetime.now() - start_time).total_seconds() * 1000)
            if remaining > 0:
                for selector in preview_selectors:
                    preview_result = self._waits.wait_for(
                        WaitCondition(type=ConditionType.ELEMENT_VISIBLE, selector=selector),
                        timeout_ms=min(remaining, 5000),
                        stability_ms=200
                    )
                    if preview_result.success:
                        preview_verified = True
                        break

        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

        return UploadResult(
            success=True,
            file_path=file_path,
            elapsed_ms=elapsed,
            preview_verified=preview_verified,
            file_size=file_size
        )

    def wait_for_download(self, trigger_action: Callable = None,
                          expected_filename: str = None,
                          timeout_ms: int = 60000) -> DownloadResult:
        """
        Wait for a download to complete

        Args:
            trigger_action: Function that triggers the download
            expected_filename: Expected filename (optional)
            timeout_ms: Maximum wait time
        """
        start_time = datetime.now()

        # Enable download behavior
        self._session.send_command('Browser.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': self._download_dir
        })

        # Record starting downloads
        initial_downloads = set(self._completed_downloads.keys())

        # Trigger download if action provided
        if trigger_action:
            try:
                trigger_action()
            except Exception as e:
                elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
                return DownloadResult(
                    success=False,
                    download_path=None,
                    elapsed_ms=elapsed,
                    error=f"Download trigger failed: {str(e)}",
                    reason=FailureReason(
                        code=ReasonCode.DOWNLOAD_FAILED,
                        message=str(e)
                    )
                )

        # Wait for download to complete
        deadline = datetime.now().timestamp() + (timeout_ms / 1000)
        download_info = None

        while datetime.now().timestamp() < deadline:
            # Check for new completed downloads
            for guid, info in self._completed_downloads.items():
                if guid not in initial_downloads:
                    if expected_filename:
                        if expected_filename in info.get('suggested_filename', ''):
                            download_info = info
                            break
                    else:
                        download_info = info
                        break

            if download_info:
                break

            # Check pending downloads
            if self._pending_downloads:
                time.sleep(0.5)
            else:
                time.sleep(0.1)

        if not download_info:
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return DownloadResult(
                success=False,
                download_path=None,
                elapsed_ms=elapsed,
                error="Download did not complete",
                reason=FailureReason(
                    code=ReasonCode.DOWNLOAD_FAILED,
                    message=f"Download timeout after {timeout_ms}ms"
                )
            )

        # Verify file exists and size is stable
        filename = download_info.get('suggested_filename', '')
        file_path = os.path.join(self._download_dir, filename)

        if not self._verify_file_stable(file_path):
            elapsed = int((datetime.now() - start_time).total_seconds() * 1000)
            return DownloadResult(
                success=False,
                download_path=file_path,
                elapsed_ms=elapsed,
                error="Downloaded file not stable",
                reason=FailureReason(
                    code=ReasonCode.FILE_NOT_READY,
                    message="File size not stable"
                )
            )

        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        elapsed = int((datetime.now() - start_time).total_seconds() * 1000)

        return DownloadResult(
            success=True,
            download_path=file_path,
            elapsed_ms=elapsed,
            file_size=file_size
        )

    def _verify_file_stable(self, file_path: str, checks: int = 3,
                           interval_ms: int = 500) -> bool:
        """Verify file exists and size is stable"""
        if not os.path.exists(file_path):
            return False

        last_size = -1
        stable_count = 0

        for _ in range(checks + 2):
            if not os.path.exists(file_path):
                return False

            current_size = os.path.getsize(file_path)

            if current_size == last_size and current_size > 0:
                stable_count += 1
                if stable_count >= checks:
                    return True
            else:
                stable_count = 0

            last_size = current_size
            time.sleep(interval_ms / 1000)

        return False

    def calculate_checksum(self, file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """Calculate file checksum"""
        if not os.path.exists(file_path):
            return None

        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def verify_download_checksum(self, file_path: str, expected_checksum: str,
                                  algorithm: str = 'md5') -> bool:
        """Verify downloaded file checksum"""
        actual = self.calculate_checksum(file_path, algorithm)
        return actual == expected_checksum

    def handle_file_chooser(self, file_paths: List[str], timeout_ms: int = 10000) -> bool:
        """
        Handle file chooser dialog

        This intercepts the Page.fileChooserOpened event and sets files.
        """
        # Enable file chooser interception
        self._session.send_command('Page.setInterceptFileChooserDialog', {
            'enabled': True
        })

        # Wait for file chooser
        event = self._session.events.wait_for(
            EventType.PAGE_FILE_CHOOSER_OPENED,
            timeout_ms=timeout_ms
        )

        if not event:
            return False

        # Handle the file chooser
        result = self._session.send_command('Page.handleFileChooser', {
            'action': 'accept',
            'files': file_paths
        })

        return result.success

    def get_pending_downloads(self) -> List[Dict]:
        """Get list of pending downloads"""
        return list(self._pending_downloads.values())

    def get_completed_downloads(self) -> List[Dict]:
        """Get list of completed downloads"""
        return list(self._completed_downloads.values())
