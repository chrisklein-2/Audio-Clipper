"""ui/taskbar.py - red recording badge on the Windows taskbar button."""
import ctypes
import os
import sys
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

CLSID_TASKBAR_LIST = "{56FDF344-FD6D-11D0-958A-006097C9A090}"
IID_TASKBAR_LIST3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"
VTBL_HR_INIT = 3
VTBL_SET_OVERLAY_ICON = 18
ICON_PX = 32


class _GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

    @classmethod
    def parse(cls, text):
        guid = cls()
        ctypes.windll.ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(guid))
        return guid


class TaskbarBadge:
    """Shows / clears a red dot on this window's taskbar button (Windows only)."""

    def __init__(self, window):
        self._window = window
        self._ptr = None
        self._set_overlay = None
        self._icons = {}
        self._failed = sys.platform != "win32"

    def _connect(self):
        if self._ptr is not None:
            return True
        if self._failed:
            return False
        try:
            clsid = _GUID.parse(CLSID_TASKBAR_LIST)
            iid = _GUID.parse(IID_TASKBAR_LIST3)
            ptr = ctypes.c_void_p()
            hr = ctypes.windll.ole32.CoCreateInstance(
                ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(ptr))
            if hr != 0 or not ptr.value:
                raise OSError("taskbar interface unavailable")
            vtbl = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
            init = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(vtbl[VTBL_HR_INIT])
            init(ptr)
            self._set_overlay = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p,
                ctypes.c_void_p, ctypes.c_wchar_p)(vtbl[VTBL_SET_OVERLAY_ICON])
            self._ptr = ptr
        except Exception:
            self._failed = True
        return self._ptr is not None

    def _hicon(self, alpha):
        if alpha in self._icons:
            return self._icons[alpha]
        img = QImage(ICON_PX, ICON_PX, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, min(alpha, 200)))
        p.drawEllipse(2, 2, 28, 28)
        p.setBrush(QColor(229, 57, 53, alpha))
        p.drawEllipse(5, 5, 22, 22)
        p.end()
        handle = None
        path = os.path.join(tempfile.gettempdir(), f"spotclip_rec_{alpha}.ico")
        if img.save(path, "ICO"):
            load = ctypes.windll.user32.LoadImageW
            load.restype = ctypes.c_void_p
            load.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint,
                             ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            handle = load(None, path, 1, ICON_PX, ICON_PX, 0x10)
        self._icons[alpha] = handle
        return handle

    def set_badge(self, alpha):
        """alpha 1..255 shows the red dot at that opacity; None clears it."""
        try:
            if not self._connect():
                return
            hicon = None if alpha is None else self._hicon(int(alpha))
            if alpha is not None and not hicon:
                return
            hwnd = int(self._window.winId())
            self._set_overlay(self._ptr, hwnd, hicon, "Recording" if hicon else None)
        except Exception:
            self._failed = True