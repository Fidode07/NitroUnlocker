import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass
from typing import *


@dataclass
class Window:
    title: str
    query: str
    hwnd: int
    executable_path: str


class ProcessHelper:
    def __init__(self) -> None:
        self.wndenumproc = ctypes.WINFUNCTYPE(wintypes.BOOL,
                                              wintypes.HWND,
                                              wintypes.LPARAM)

        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        self.psapi = ctypes.WinDLL('psapi', use_last_error=True)

        self.user32.EnumWindows.argtypes = [
            self.wndenumproc,
            wintypes.LPARAM]
        self.user32.GetWindowTextLengthW.argtypes = [
            wintypes.HWND]
        self.user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int]

    def find_window_by_title(self, title: str, only_contains: bool = True) -> Union[List[Window], Window]:
        if not only_contains:
            hwnd: int = ctypes.windll.user32.FindWindowA(None, title)
            return Window(title=title,
                          query=title,
                          hwnd=hwnd,
                          executable_path=self.get_exec_path_by_hwnd(hwnd))
        tg_hwnd: List[Window] = []

        def enum_func(cur_hwnd: int, _: int) -> int:
            if self.user32.IsWindowVisible(cur_hwnd):
                length: int = self.user32.GetWindowTextLengthW(cur_hwnd) + 1
                buffer = ctypes.create_unicode_buffer(length)
                self.user32.GetWindowTextW(cur_hwnd, buffer, length)
                val: str = str(buffer.value).lower()
                if val and title.lower() in val:
                    tg_hwnd.append(Window(title=title,
                                          query=title,
                                          hwnd=cur_hwnd,
                                          executable_path=self.get_exec_path_by_hwnd(cur_hwnd)))
            return 1

        self.user32.EnumWindows(self.wndenumproc(enum_func), 42)
        return tg_hwnd

    def get_exec_path_by_hwnd(self, hwnd: int) -> str:
        max_path_length = 260  # Just pray nobody has a longer path ...
        lp_filename = ctypes.create_unicode_buffer(max_path_length)

        process_id = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

        process_handle = self.kernel32.OpenProcess(
            wintypes.DWORD(0x0400 | 0x0010), False, process_id)
        if not process_handle:
            return ""

        self.psapi.GetModuleFileNameExW(
            process_handle, None, lp_filename, max_path_length)
        self.kernel32.CloseHandle(process_handle)

        return lp_filename.value

    def kill_proc_by_hwnd(self, hwnd: int, timeout: float = 0) -> bool:
        process_id = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

        process_handle = self.kernel32.OpenProcess(
            0x0001 | 0x0400 | 0x0010, False, process_id)
        if not process_handle:
            return False

        termination_result = self.kernel32.TerminateProcess(process_handle, 0)
        self.kernel32.CloseHandle(process_handle)
        time.sleep(timeout)
        return bool(termination_result)
