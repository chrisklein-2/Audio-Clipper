"""
waveform/dropping.py - DropMixin: drop audio files onto the waveform.

Mixed into WaveformView. Emits filesDropped(paths, seconds); -1 is never sent
from here, but the main window treats a negative time as "append to the end".
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame


class DropMixin:

    # Call once from WaveformView.__init__
    def _init_drop(self):
        self.drop_filter = None           # set by the main window: mime -> bool
        self.setAcceptDrops(True)
        self._drop_line = QFrame(self)    # marker that follows the mouse
        self._drop_line.setStyleSheet("background: #f5a623;")
        self._drop_line.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._drop_line.hide()


    # Seconds into the clip at a widget x position
    def _seconds_at(self, x):
        return max(0.0, min(self.x2t(x), self.duration()))


    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls() and (self.drop_filter is None or self.drop_filter(mime)):
            event.acceptProposedAction()
        else:
            event.ignore()


    def dragMoveEvent(self, event):
        if self.duration() > 0:
            x = int(event.position().x())
            self._drop_line.setGeometry(x - 1, 0, 2, self.height())
            self._drop_line.show()
            self._drop_line.raise_()
        event.acceptProposedAction()


    def dragLeaveEvent(self, event):
        self._drop_line.hide()


    def dropEvent(self, event):
        self._drop_line.hide()
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if not paths:
            event.ignore()
            return
        seconds = self._seconds_at(event.position().x())
        event.acceptProposedAction()
        self.filesDropped.emit(paths, seconds)