"""
Window Manager - Quản lý vị trí và kích thước cửa sổ trình duyệt
Sắp xếp các cửa sổ theo grid, không chồng lên nhau
"""
import threading
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class WindowConfig:
    """Cấu hình cửa sổ"""
    width: int = 400
    height: int = 300
    margin: int = 5  # Khoảng cách giữa các cửa sổ


class WindowManager:
    """
    Quản lý vị trí cửa sổ theo grid

    Usage:
        manager = WindowManager.get_instance()
        slot = manager.acquire_slot()  # Lấy vị trí
        x, y, w, h = manager.get_bounds(slot)  # Lấy bounds
        # ... dùng xong ...
        manager.release_slot(slot)  # Trả lại slot
    """

    _instance = None
    _lock = threading.Lock()

    # Kích thước màn hình mặc định - auto detect nếu có thể
    SCREEN_WIDTH = 5120  # Default cho ultrawide
    SCREEN_HEIGHT = 1440

    # Kích thước cửa sổ mặc định (trước khi scale)
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 1500
    MARGIN = 10

    # Offset để tránh taskbar
    TOP_OFFSET = 0
    LEFT_OFFSET = 0

    def __init__(self):
        self._slots: Dict[int, bool] = {}  # slot_id -> is_occupied
        self._max_slots = 0
        self._cols = 0
        self._rows = 0
        self._auto_detect_screen_size()
        self._recalculate_grid()

    def _auto_detect_screen_size(self):
        """Tự động phát hiện kích thước màn hình"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Ẩn cửa sổ
            self.SCREEN_WIDTH = root.winfo_screenwidth()
            self.SCREEN_HEIGHT = root.winfo_screenheight()
            root.destroy()
            print(f"[WindowManager] Auto-detected screen: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT}")
        except Exception as e:
            print(f"[WindowManager] Could not detect screen size, using default: {e}")

    @classmethod
    def get_instance(cls) -> 'WindowManager':
        """Get singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = WindowManager()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton để re-detect screen size"""
        with cls._lock:
            cls._instance = None

    def _recalculate_grid(self):
        """Tính lại số cột/hàng dựa trên kích thước màn hình"""
        usable_width = self.SCREEN_WIDTH - self.LEFT_OFFSET
        usable_height = self.SCREEN_HEIGHT - self.TOP_OFFSET - 40  # Trừ taskbar

        self._cols = max(1, usable_width // (self.WINDOW_WIDTH + self.MARGIN))
        self._rows = max(1, usable_height // (self.WINDOW_HEIGHT + self.MARGIN))
        self._max_slots = self._cols * self._rows

        # Initialize slots
        for i in range(self._max_slots):
            if i not in self._slots:
                self._slots[i] = False

    def set_screen_size(self, width: int, height: int):
        """Cập nhật kích thước màn hình"""
        self.SCREEN_WIDTH = width
        self.SCREEN_HEIGHT = height
        self._recalculate_grid()

    def set_window_size(self, width: int, height: int):
        """Cập nhật kích thước cửa sổ"""
        self.WINDOW_WIDTH = width
        self.WINDOW_HEIGHT = height
        self._recalculate_grid()

    def acquire_slot(self) -> int:
        """
        Lấy slot trống cho cửa sổ mới
        Returns slot_id hoặc -1 nếu hết slot
        """
        with self._lock:
            for slot_id in range(self._max_slots):
                if not self._slots.get(slot_id, False):
                    self._slots[slot_id] = True
                    return slot_id

            # Nếu hết slot, mở rộng grid (cửa sổ sẽ đè nhau)
            new_slot = self._max_slots
            self._max_slots += 1
            self._slots[new_slot] = True
            return new_slot

    def release_slot(self, slot_id: int):
        """Trả lại slot khi đóng cửa sổ"""
        with self._lock:
            if slot_id in self._slots:
                self._slots[slot_id] = False

    def get_bounds(self, slot_id: int) -> Tuple[int, int, int, int]:
        """
        Tính toán vị trí và kích thước cho slot

        Returns: (x, y, width, height)
        """
        if slot_id < 0:
            return (0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        # Tính row và col từ slot_id
        col = slot_id % self._cols
        row = (slot_id // self._cols) % self._rows

        x = self.LEFT_OFFSET + col * (self.WINDOW_WIDTH + self.MARGIN)
        y = self.TOP_OFFSET + row * (self.WINDOW_HEIGHT + self.MARGIN)

        return (x, y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

    def get_grid_info(self) -> Dict:
        """Lấy thông tin grid hiện tại"""
        return {
            'cols': self._cols,
            'rows': self._rows,
            'max_slots': self._max_slots,
            'used_slots': sum(1 for v in self._slots.values() if v),
            'window_size': (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
            'screen_size': (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        }

    def reset(self):
        """Reset tất cả slots"""
        with self._lock:
            for slot_id in self._slots:
                self._slots[slot_id] = False


# Convenience functions
def get_window_manager() -> WindowManager:
    """Get singleton window manager instance"""
    return WindowManager.get_instance()


def acquire_window_slot() -> int:
    """Acquire a window slot"""
    manager = get_window_manager()
    slot = manager.acquire_slot()
    print(f"[WindowManager] Acquired slot {slot}, grid: {manager._cols}x{manager._rows}, screen: {manager.SCREEN_WIDTH}x{manager.SCREEN_HEIGHT}")
    return slot


def release_window_slot(slot_id: int):
    """Release a window slot"""
    get_window_manager().release_slot(slot_id)


def get_window_bounds(slot_id: int) -> Tuple[int, int, int, int]:
    """Get bounds for a slot"""
    bounds = get_window_manager().get_bounds(slot_id)
    print(f"[WindowManager] get_window_bounds(slot={slot_id}) -> x={bounds[0]}, y={bounds[1]}, w={bounds[2]}, h={bounds[3]}")
    return bounds


def configure_window_size(width: int = 400, height: int = 320):
    """Configure default window size"""
    get_window_manager().set_window_size(width, height)


def configure_screen_size(width: int = 1920, height: int = 1080):
    """Configure screen size"""
    get_window_manager().set_screen_size(width, height)
