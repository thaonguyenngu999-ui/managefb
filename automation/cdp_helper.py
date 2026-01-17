"""
CDP Helper - High-level automation functions for tabs
Wraps CDPClientMAX with easy-to-use functions
"""
import time
import random
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .cdp_max import CDPClientMAX, CDPClientConfig, Postcondition
from .human_behavior import HumanBehavior


@dataclass
class CDPHelperResult:
    """Result from CDP helper operations"""
    success: bool
    data: Any = None
    error: Optional[str] = None


class CDPHelper:
    """
    High-level CDP helper for automation tasks

    Usage:
        helper = CDPHelper()
        if helper.connect(remote_port):
            helper.navigate("https://facebook.com")
            helper.click_by_aria_label("Viết")
            helper.type_human_like("Hello world")
            helper.click_by_aria_label("Đăng")
            helper.close()
    """

    def __init__(self, remote_port: int = None, ws_url: str = None):
        self._client: Optional[CDPClientMAX] = None
        self._remote_port = remote_port
        self._ws_url = ws_url
        self._connected = False

    @property
    def client(self) -> Optional[CDPClientMAX]:
        return self._client

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client and self._client.is_connected

    def connect(self, remote_port: int = None, ws_url: str = None) -> bool:
        """
        Connect to browser CDP

        Args:
            remote_port: CDP debug port (used if ws_url not provided)
            ws_url: Direct WebSocket URL from browser API (preferred)
        """
        # Prefer ws_url (avoids 403 Forbidden from Chrome origin check)
        url = ws_url or self._ws_url
        port = remote_port or self._remote_port

        if not url and not port:
            return False

        if port:
            self._remote_port = port
        if url:
            self._ws_url = url

        config = CDPClientConfig(
            remote_port=port or 0,
            ws_url=url,
            auto_reconnect=True,
            enable_watchdog=True,
            enable_recovery=True,
            step_timeout_ms=15000,
            state_timeout_ms=30000
        )

        self._client = CDPClientMAX(config)
        success, reason = self._client.connect()

        if success:
            self._connected = True
            return True
        else:
            self._connected = False
            print(f"[CDP] Connect failed: {reason.message if reason else 'unknown'}")
            return False

    def close(self):
        """Close CDP connection"""
        if self._client:
            self._client.close()
            self._client = None
        self._connected = False

    # ==================== NAVIGATION ====================

    def navigate(self, url: str, wait_for_load: bool = True) -> bool:
        """Navigate to URL"""
        if not self.is_connected:
            return False

        result = self._client.navigate(url, wait_until='load' if wait_for_load else 'domcontentloaded')

        if result.success and wait_for_load:
            # Human-like delay after navigation
            HumanBehavior.random_delay(1.0, 2.5)

        return result.success

    def wait_for_page_ready(self, timeout_ms: int = 15000) -> bool:
        """Wait for page to be fully loaded"""
        if not self.is_connected:
            return False

        result = self._client.wait_for_network_idle(timeout_ms=timeout_ms)
        return result.success

    def get_current_url(self) -> Optional[str]:
        """Get current page URL"""
        if not self.is_connected:
            return None
        return self._client.get_current_url()

    # ==================== ELEMENT INTERACTION ====================

    def click_by_aria_label(self, label: str, wait_after: bool = True) -> bool:
        """Click element by aria-label"""
        if not self.is_connected:
            return False

        locator = self._client.by_aria_label(label)
        if not self._client.exists(locator):
            return False

        result = self._client.click(locator)

        if result.success and wait_after:
            HumanBehavior.random_delay(0.5, 1.0)

        return result.success

    def click_by_text(self, text: str, wait_after: bool = True) -> bool:
        """Click element by text content"""
        if not self.is_connected:
            return False

        locator = self._client.by_text(text)
        if not self._client.exists(locator):
            return False

        result = self._client.click(locator)

        if result.success and wait_after:
            HumanBehavior.random_delay(0.5, 1.0)

        return result.success

    def click_by_css(self, selector: str, wait_after: bool = True) -> bool:
        """Click element by CSS selector"""
        if not self.is_connected:
            return False

        locator = self._client.by_css(selector)
        if not self._client.exists(locator):
            return False

        result = self._client.click(locator)

        if result.success and wait_after:
            HumanBehavior.random_delay(0.5, 1.0)

        return result.success

    def exists(self, selector: str = None, aria_label: str = None, text: str = None) -> bool:
        """Check if element exists"""
        if not self.is_connected:
            return False

        if aria_label:
            locator = self._client.by_aria_label(aria_label)
        elif text:
            locator = self._client.by_text(text)
        elif selector:
            locator = self._client.by_css(selector)
        else:
            return False

        return self._client.exists(locator)

    def is_visible(self, selector: str = None, aria_label: str = None) -> bool:
        """Check if element is visible"""
        if not self.is_connected:
            return False

        if aria_label:
            locator = self._client.by_aria_label(aria_label)
        elif selector:
            locator = self._client.by_css(selector)
        else:
            return False

        return self._client.is_visible(locator)

    # ==================== TYPING ====================

    def type_human_like(self, text: str, selector: str = None) -> bool:
        """
        Type text with human-like behavior

        If selector is None, types into currently focused element
        """
        if not self.is_connected:
            return False

        if selector:
            # Focus element first
            escaped_selector = selector.replace("'", "\\'")
            focus_js = f'''
                (function() {{
                    let el = document.querySelector('{escaped_selector}');
                    if (el) {{
                        el.focus();
                        return true;
                    }}
                    return false;
                }})()
            '''
            if not self._client.execute(focus_js):
                return False

        # Type character by character for human-like behavior
        # For long text, use execCommand for performance
        if len(text) > 200:
            return self._type_fast(text)
        else:
            return self._type_with_typos(text)

    def _type_fast(self, text: str) -> bool:
        """
        Type text nhanh hơn nhưng vẫn human-like (từng ký tự với delay ngắn)
        Dùng cho text dài > 200 chars
        """
        try:
            for char in text:
                self._client.session.send_command('Input.insertText', {'text': char})
                # Delay ngắn hơn _type_with_typos nhưng vẫn có variation
                if char in ' .,!?;:\n':
                    time.sleep(random.uniform(0.03, 0.08))
                else:
                    time.sleep(random.uniform(0.015, 0.04))
            return True
        except Exception as e:
            print(f"[CDPHelper] _type_fast error: {e}")
            return False

    def _type_with_typos(self, text: str) -> bool:
        """Type with occasional typos and corrections"""
        # Typo map for adjacent keys
        typo_map = {
            'a': ['s', 'q'], 'b': ['v', 'n'], 'c': ['x', 'v'],
            'd': ['s', 'f'], 'e': ['w', 'r'], 'f': ['d', 'g'],
            'g': ['f', 'h'], 'h': ['g', 'j'], 'i': ['u', 'o'],
            'j': ['h', 'k'], 'k': ['j', 'l'], 'l': ['k', 'o'],
            'm': ['n', 'k'], 'n': ['b', 'm'], 'o': ['i', 'p'],
            'p': ['o', 'l'], 'r': ['e', 't'], 's': ['a', 'd'],
            't': ['r', 'y'], 'u': ['y', 'i'], 'v': ['c', 'b'],
            'w': ['q', 'e'], 'x': ['z', 'c'], 'y': ['t', 'u'],
        }

        for char in text:
            # 3% chance of typo for lowercase letters
            if char.lower() in typo_map and random.random() < 0.03:
                # Type wrong character
                wrong_char = random.choice(typo_map[char.lower()])
                self._client.session.send_command('Input.insertText', {'text': wrong_char})
                time.sleep(random.uniform(0.1, 0.3))

                # Backspace to correct
                self._client.session.send_command('Input.dispatchKeyEvent', {
                    'type': 'keyDown', 'key': 'Backspace', 'code': 'Backspace'
                })
                self._client.session.send_command('Input.dispatchKeyEvent', {
                    'type': 'keyUp', 'key': 'Backspace', 'code': 'Backspace'
                })
                time.sleep(random.uniform(0.1, 0.2))

            # Type correct character
            self._client.session.send_command('Input.insertText', {'text': char})

            # Variable delay based on character type
            if char in ' .,!?':
                time.sleep(random.uniform(0.08, 0.2))
            elif char == '\n':
                time.sleep(random.uniform(0.3, 0.6))
            else:
                time.sleep(random.uniform(0.03, 0.1))

        return True

    # ==================== SCROLLING ====================

    def scroll_down(self, amount: int = None) -> bool:
        """Scroll down with human-like behavior"""
        if not self.is_connected:
            return False

        if amount is None:
            amount = random.randint(200, 500)

        # Scroll in steps for human-like effect
        steps = random.randint(3, 6)
        step_amount = amount // steps

        for _ in range(steps):
            self._client.execute(f'window.scrollBy(0, {step_amount})')
            time.sleep(random.uniform(0.05, 0.15))

        HumanBehavior.random_delay(0.3, 0.7)
        return True

    def scroll_to_element(self, selector: str = None, aria_label: str = None) -> bool:
        """Scroll element into view"""
        if not self.is_connected:
            return False

        if aria_label:
            locator = self._client.by_aria_label(aria_label)
        elif selector:
            locator = self._client.by_css(selector)
        else:
            return False

        result = self._client.scroll_to(locator)
        if result.success:
            HumanBehavior.random_delay(0.3, 0.6)
        return result.success

    # ==================== JAVASCRIPT ====================

    def execute_js(self, expression: str) -> Any:
        """Execute JavaScript and return result"""
        if not self.is_connected:
            return None
        return self._client.evaluate(expression)

    def execute(self, script: str) -> bool:
        """Execute JavaScript"""
        if not self.is_connected:
            return False
        return self._client.execute(script)

    # ==================== SCREENSHOTS ====================

    def take_screenshot(self, reason: str = 'manual') -> Optional[str]:
        """Take screenshot, returns base64 data"""
        if not self.is_connected:
            return None
        return self._client.take_screenshot(reason=reason)

    # ==================== WINDOW MANAGEMENT ====================

    def set_window_bounds(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Set browser window position and size using CDP Browser domain

        Args:
            x: Window left position
            y: Window top position
            width: Window width
            height: Window height
        """
        if not self.is_connected:
            return False

        try:
            # Get window ID for current target
            result = self._client.session.send_command('Browser.getWindowForTarget', {})
            if not result or 'windowId' not in result:
                print("[CDP] Failed to get window ID")
                return False

            window_id = result['windowId']

            # Set window bounds
            bounds = {
                'left': x,
                'top': y,
                'width': width,
                'height': height,
                'windowState': 'normal'
            }

            self._client.session.send_command('Browser.setWindowBounds', {
                'windowId': window_id,
                'bounds': bounds
            })

            return True

        except Exception as e:
            print(f"[CDP] set_window_bounds error: {e}")
            return False

    def get_window_bounds(self) -> Optional[Dict]:
        """Get current window bounds"""
        if not self.is_connected:
            return None

        try:
            result = self._client.session.send_command('Browser.getWindowForTarget', {})
            if not result or 'windowId' not in result:
                return None

            window_id = result['windowId']
            bounds_result = self._client.session.send_command('Browser.getWindowBounds', {
                'windowId': window_id
            })

            return bounds_result.get('bounds')

        except Exception as e:
            print(f"[CDP] get_window_bounds error: {e}")
            return None

    # ==================== HIGH-LEVEL ACTIONS ====================

    def click_like_button(self) -> bool:
        """Click the Like button on current page (Facebook post)"""
        if not self.is_connected:
            return False

        # Specific JS to find and click the MAIN post's Like button (not comment likes)
        js_click_like = '''
            (function() {
                // Method 1: Tìm nút Like theo aria-label
                let likeButtons = document.querySelectorAll('[role="button"][aria-label*="Thích"], [role="button"][aria-label*="Like"]');

                for (let btn of likeButtons) {
                    let label = btn.getAttribute('aria-label') || '';
                    // Bỏ qua nút đã like (Bỏ thích/Unlike)
                    if (label.includes('Bỏ thích') || label.includes('Unlike')) continue;

                    let rect = btn.getBoundingClientRect();
                    // Nút Like chính thường lớn và trong viewport
                    if (rect.width > 20 && rect.height > 15 && rect.top > 0 && rect.top < window.innerHeight) {
                        btn.click();
                        return 'clicked_aria';
                    }
                }

                // Method 2: Tìm theo text "Thích" trong action bar
                let spans = document.querySelectorAll('span');
                for (let span of spans) {
                    let text = (span.innerText || '').trim();
                    if (text === 'Thích' || text === 'Like') {
                        // Tìm button parent
                        let btn = span.closest('[role="button"]') || span.closest('div[tabindex]');
                        if (btn) {
                            let rect = btn.getBoundingClientRect();
                            if (rect.top > 0 && rect.top < window.innerHeight) {
                                btn.click();
                                return 'clicked_text';
                            }
                        }
                    }
                }

                // Method 3: Tìm theo data-testid
                let testIdBtn = document.querySelector('[data-testid*="like"]') ||
                               document.querySelector('[data-testid*="reaction"]');
                if (testIdBtn) {
                    testIdBtn.click();
                    return 'clicked_testid';
                }

                // Method 4: Tìm trong action bar (chứa Bình luận, Chia sẻ)
                let divs = document.querySelectorAll('div[role="button"]');
                for (let div of divs) {
                    let parent = div.parentElement?.parentElement;
                    if (parent) {
                        let parentText = parent.innerText || '';
                        if ((parentText.includes('Bình luận') || parentText.includes('Comment')) &&
                            (parentText.includes('Chia sẻ') || parentText.includes('Share'))) {
                            // Đây là action bar, click div đầu tiên (thường là Like)
                            let text = (div.innerText || '').trim();
                            if (text === 'Thích' || text === 'Like' || text === '') {
                                div.click();
                                return 'clicked_actionbar';
                            }
                        }
                    }
                }

                return 'not_found';
            })()
        '''

        result = self._client.execute(js_click_like)
        if result and 'clicked' in str(result):
            HumanBehavior.random_delay(0.3, 0.6)
            return True

        return False

    def open_post_composer(self) -> bool:
        """Open post composer dialog on Facebook group page"""
        if not self.is_connected:
            return False

        # Try different selectors
        for label in ["Viết gì đó...", "Viết", "Write something...", "Write"]:
            if self.click_by_aria_label(label, wait_after=False):
                HumanBehavior.random_delay(0.8, 1.5)
                return True

        # Try clicking textbox directly
        if self.click_by_css('[role="textbox"]', wait_after=False):
            HumanBehavior.random_delay(0.8, 1.5)
            return True

        return False

    def submit_post(self) -> bool:
        """Click post/submit button on Facebook"""
        if not self.is_connected:
            return False

        # Try different post button labels
        for label in ["Đăng", "Post", "Xuất bản", "Publish"]:
            locator = self._client.by_aria_label(label)
            if self._client.exists(locator):
                # Postcondition: dialog closes
                postcond = Postcondition(
                    check=lambda: not self._client.exists(
                        self._client.by_css('[role="textbox"][contenteditable="true"]')
                    ),
                    description="Post dialog closed",
                    timeout_ms=15000
                )

                result = self._client.click(locator, postcondition=postcond)
                if result.success:
                    return True

        # Try text-based buttons
        for text in ["Đăng", "Post"]:
            locator = self._client.by_text(text)
            if self._client.exists(locator):
                result = self._client.click(locator)
                if result.success:
                    HumanBehavior.random_delay(2.0, 4.0)
                    return True

        # Fallback to JS
        js = '''
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
        if self._client.execute(js):
            HumanBehavior.random_delay(2.0, 4.0)
            return True

        return False

    def post_to_group(self, content: str, images: List[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Post content to current Facebook group

        Returns: (success, post_url)
        """
        if not self.is_connected:
            return False, None

        # Wait for page ready
        self.wait_for_page_ready()

        # Open composer
        if not self.open_post_composer():
            return False, None

        # Focus vào textbox trước
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

        if not self._client.execute(focus_js):
            return False, None

        # Gõ từng ký tự như người thật (hoạt động với Lexical editor)
        if not self.type_human_like(content):
            return False, None

        # Human-like think pause
        HumanBehavior.think_pause()

        # TODO: Handle image uploads if images provided

        # Submit post
        if not self.submit_post():
            return False, None

        # Get post URL if available
        post_url = self.get_current_url()

        return True, post_url


# ==================== FACTORY FUNCTIONS ====================

def create_cdp_helper(remote_port: int) -> Optional[CDPHelper]:
    """Create and connect a CDP helper"""
    helper = CDPHelper()
    if helper.connect(remote_port):
        return helper
    return None


def get_remote_port_from_browser(profile_uuid: str) -> Optional[int]:
    """Open browser and get remote port"""
    from api_service import api

    result = api.open_browser(profile_uuid)

    if result.get('type') == 'error':
        return None

    data = result.get('data', {})
    remote_port = data.get('remote_port')
    ws_url = data.get('web_socket', '')

    if not remote_port and ws_url:
        match = re.search(r':(\d+)/', ws_url)
        if match:
            remote_port = int(match.group(1))

    return remote_port
