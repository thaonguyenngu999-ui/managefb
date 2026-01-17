"""
Human-like Automation Utilities
Tạo các pattern giống người thật để tránh detection
"""
import random
import time
from typing import Tuple, List
from datetime import datetime


class HumanBehavior:
    """
    Tạo hành vi giống người thật
    - Random delays với distribution tự nhiên
    - Typing patterns
    - Mouse movement simulation (conceptual)
    - Time-of-day awareness
    """

    @staticmethod
    def random_delay(min_sec: float = 0.5, max_sec: float = 2.0,
                    distribution: str = "normal") -> float:
        """
        Delay ngẫu nhiên với distribution tự nhiên

        Người thật không delay đều - thường có:
        - Phần lớn delays ngắn
        - Đôi khi pause dài hơn (đọc, suy nghĩ)
        """
        if distribution == "normal":
            # Normal distribution - phần lớn ở giữa
            mean = (min_sec + max_sec) / 2
            std = (max_sec - min_sec) / 4
            delay = random.gauss(mean, std)
            delay = max(min_sec, min(max_sec, delay))
        elif distribution == "exponential":
            # Exponential - phần lớn ngắn, đôi khi dài
            scale = (max_sec - min_sec) / 3
            delay = min_sec + random.expovariate(1 / scale)
            delay = min(max_sec, delay)
        else:
            # Uniform
            delay = random.uniform(min_sec, max_sec)

        time.sleep(delay)
        return delay

    @staticmethod
    def typing_delay() -> float:
        """Delay giữa các keystroke - người thật type 40-80 WPM"""
        # ~200-400ms per character với variation
        delay = random.gauss(0.1, 0.03)
        delay = max(0.05, min(0.3, delay))
        time.sleep(delay)
        return delay

    @staticmethod
    def think_pause() -> float:
        """Pause như đang suy nghĩ - 1-5 giây"""
        delay = random.gauss(2.5, 1.0)
        delay = max(1.0, min(5.0, delay))
        time.sleep(delay)
        return delay

    @staticmethod
    def reading_time(text_length: int) -> float:
        """
        Thời gian đọc text
        Người thật đọc ~200-300 words/minute
        """
        # Assume ~5 chars per word
        words = text_length / 5
        reading_wpm = random.uniform(200, 300)
        minutes = words / reading_wpm
        delay = minutes * 60

        # Min 0.5s, max 10s
        delay = max(0.5, min(10.0, delay))
        time.sleep(delay)
        return delay

    @staticmethod
    def scroll_pattern() -> List[Tuple[int, float]]:
        """
        Pattern scroll như người thật
        Returns: [(pixels, delay), ...]

        Người thật không scroll đều - scroll một chút, pause đọc, scroll tiếp
        """
        patterns = []
        total_scroll = random.randint(500, 1500)
        scrolled = 0

        while scrolled < total_scroll:
            # Scroll amount - thường 100-400px
            amount = random.randint(100, 400)
            amount = min(amount, total_scroll - scrolled)

            # Pause sau scroll - đọc content
            pause = random.uniform(0.5, 2.0)

            patterns.append((amount, pause))
            scrolled += amount

        return patterns

    @staticmethod
    def is_active_hours() -> bool:
        """
        Kiểm tra có phải giờ hoạt động bình thường không
        Người thật thường online 7h-23h
        """
        hour = datetime.now().hour
        return 7 <= hour <= 23

    @staticmethod
    def session_break_needed(actions_count: int, session_start: datetime) -> bool:
        """
        Kiểm tra có cần nghỉ giữa session không

        Người thật không làm liên tục - sau 20-30 actions hoặc 30-60 phút
        sẽ nghỉ ngắn
        """
        # Nghỉ sau mỗi 20-40 actions
        if actions_count > random.randint(20, 40):
            return True

        # Nghỉ sau 30-60 phút
        elapsed = (datetime.now() - session_start).total_seconds() / 60
        if elapsed > random.randint(30, 60):
            return True

        return False

    @staticmethod
    def take_break(short: bool = True) -> float:
        """Nghỉ ngắn hoặc dài"""
        if short:
            # Nghỉ ngắn 30s - 2 phút
            delay = random.uniform(30, 120)
        else:
            # Nghỉ dài 5-15 phút
            delay = random.uniform(300, 900)

        time.sleep(delay)
        return delay

    @staticmethod
    def add_jitter(base_delay: float, jitter_percent: float = 0.2) -> float:
        """
        Thêm jitter vào delay để tránh pattern detection
        """
        jitter = base_delay * jitter_percent
        actual = base_delay + random.uniform(-jitter, jitter)
        return max(0.1, actual)


class AntiDetection:
    """
    Các kỹ thuật anti-detection
    """

    @staticmethod
    def randomize_viewport_scroll(cdp_client) -> bool:
        """
        Scroll ngẫu nhiên trong viewport trước khi action
        Giống người thật đang nhìn quanh trang
        """
        try:
            # Random scroll nhỏ
            scroll_y = random.randint(-100, 200)
            js = f'window.scrollBy(0, {scroll_y})'
            cdp_client.execute_js(js)
            HumanBehavior.random_delay(0.3, 0.8)
            return True
        except:
            return False

    @staticmethod
    def hover_before_click(cdp_client, selector: str) -> bool:
        """
        Hover trước khi click - người thật luôn làm thế
        """
        try:
            js = f'''
                (function() {{
                    let el = document.querySelector('{selector}');
                    if (!el) return false;

                    // Dispatch mouseover event
                    el.dispatchEvent(new MouseEvent('mouseover', {{
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }}));

                    return true;
                }})()
            '''
            result = cdp_client.execute_js(js)
            if result.success:
                HumanBehavior.random_delay(0.1, 0.3)
            return result.success and result.data
        except:
            return False

    @staticmethod
    def gradual_type(cdp_client, selector: str, text: str) -> bool:
        """
        Type từng ký tự với delay tự nhiên
        Không paste cả đoạn text
        """
        try:
            # Focus element first
            js = f'''
                (function() {{
                    let el = document.querySelector('{selector}');
                    if (!el) return false;
                    el.focus();
                    return true;
                }})()
            '''
            focus_result = cdp_client.execute_js(js)
            if not (focus_result.success and focus_result.data):
                return False

            HumanBehavior.random_delay(0.2, 0.5)

            # Type character by character
            for i, char in enumerate(text):
                # Escape special characters
                escaped = char.replace('\\', '\\\\').replace("'", "\\'")

                type_js = f'''
                    (function() {{
                        let el = document.activeElement;
                        if (!el) return false;

                        // Create and dispatch input event
                        let event = new InputEvent('input', {{
                            bubbles: true,
                            cancelable: true,
                            inputType: 'insertText',
                            data: '{escaped}'
                        }});

                        // For contenteditable
                        if (el.contentEditable === 'true') {{
                            document.execCommand('insertText', false, '{escaped}');
                        }} else {{
                            el.value = (el.value || '') + '{escaped}';
                            el.dispatchEvent(event);
                        }}

                        return true;
                    }})()
                '''
                cdp_client.execute_js(type_js)

                # Human-like typing delay
                HumanBehavior.typing_delay()

                # Occasionally pause longer (thinking)
                if random.random() < 0.05:
                    HumanBehavior.random_delay(0.5, 1.5)

            return True

        except Exception as e:
            print(f"Gradual type error: {e}")
            return False

    @staticmethod
    def natural_click(cdp_client, selector: str) -> bool:
        """
        Click với các bước tự nhiên:
        1. Scroll element into view
        2. Hover
        3. Small delay
        4. Click
        """
        try:
            # 1. Scroll into view
            js = f'''
                (function() {{
                    let el = document.querySelector('{selector}');
                    if (!el) return false;
                    el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    return true;
                }})()
            '''
            cdp_client.execute_js(js)
            HumanBehavior.random_delay(0.3, 0.6)

            # 2. Hover
            AntiDetection.hover_before_click(cdp_client, selector)

            # 3. Click
            click_js = f'''
                (function() {{
                    let el = document.querySelector('{selector}');
                    if (!el) return false;
                    el.click();
                    return true;
                }})()
            '''
            result = cdp_client.execute_js(click_js)
            return result.success and result.data

        except:
            return False


class WaitStrategy:
    """
    Chiến lược wait thông minh - anti-flake
    """

    @staticmethod
    def debounced_wait(cdp_client, condition_fn, timeout_ms: int = 10000,
                      stable_ms: int = 500) -> bool:
        """
        Wait với debounce - condition phải đúng liên tục trong stable_ms
        Tránh false positive từ UI đang transition
        """
        start = time.time()
        stable_start = None

        while (time.time() - start) * 1000 < timeout_ms:
            try:
                if condition_fn():
                    if stable_start is None:
                        stable_start = time.time()
                    elif (time.time() - stable_start) * 1000 >= stable_ms:
                        return True
                else:
                    stable_start = None  # Reset
            except:
                stable_start = None

            # Poll with jitter
            poll_interval = HumanBehavior.add_jitter(0.1, 0.3)
            time.sleep(poll_interval)

        return False

    @staticmethod
    def wait_for_network_idle(cdp_client, idle_time_ms: int = 1000,
                             timeout_ms: int = 30000) -> bool:
        """
        Wait cho network idle - không có request nào trong idle_time_ms
        """
        # Simplified - just wait for document ready + extra time
        start = time.time()

        while (time.time() - start) * 1000 < timeout_ms:
            try:
                result = cdp_client.execute_js('document.readyState')
                if result.success and result.data == 'complete':
                    time.sleep(idle_time_ms / 1000)
                    return True
            except:
                pass

            time.sleep(0.2)

        return False

    @staticmethod
    def wait_for_stable_dom(cdp_client, selector: str, timeout_ms: int = 10000) -> bool:
        """
        Wait cho DOM element ổn định (không thay đổi trong 500ms)
        """
        start = time.time()
        last_html = None
        stable_start = None

        while (time.time() - start) * 1000 < timeout_ms:
            try:
                js = f'''
                    (function() {{
                        let el = document.querySelector('{selector}');
                        return el ? el.outerHTML.substring(0, 200) : null;
                    }})()
                '''
                result = cdp_client.execute_js(js)

                if result.success and result.data:
                    if result.data == last_html:
                        if stable_start is None:
                            stable_start = time.time()
                        elif (time.time() - stable_start) * 1000 >= 500:
                            return True
                    else:
                        last_html = result.data
                        stable_start = None
            except:
                stable_start = None

            time.sleep(0.1)

        return False
