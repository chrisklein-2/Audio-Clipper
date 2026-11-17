"""
waveform/view.py - WaveformView: state and the peak cache.

The behaviour is split into mixins:
  zoom.py       the visible window and time <-> pixel maths
  selection.py  selection, in/out marks, playhead
  input.py      mouse, wheel, keyboard, context menu
  dropping.py   drag and drop of audio files
All drawing lives in painter.py.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from .painter import paint
from .zoom import ZoomMixin
from .selection import SelectionMixin
from .input import InputMixin
from .dropping import DropMixin


class WaveformView(ZoomMixin, SelectionMixin, InputMixin, DropMixin, QWidget):
    selectionChanged = Signal()
    playheadMoved = Signal(float)
    viewChanged = Signal()
    blockSelected = Signal(int)      # kept-piece index, or -1 for a deleted gap
    filesDropped = Signal(list, float)   # (file paths, seconds into the clip)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.setMinimumWidth(320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # model
        self.timeline = None
        self.bookmarks = []

        # live recording view
        self.live_mono = None
        self.live_label = ""
        self.live_marks = []
        self.live_env = None

        # fades shown on the waveform
        self.fade_ms = 500.0
        self.end_fade_s = 0.0

        # playhead, selection, zoom window
        self.playhead = 0.0
        self.sel_a = self.sel_b = None
        self.view_start = 0.0
        self.view_end = 1.0
        self.context_actions = []
        self.context_time = None

        # mouse state
        self._drag = None
        self._pan = None
        self._press_x = 0.0
        self._marking = False

        # peak cache
        self.peaks = None
        self._peaks_key = None

        self._init_drop()


    # ---- model / mode ----------------------------------------------------


    # Accept a list of source-time bookmarks to display on the ruler
    def set_bookmarks(self, bookmarks):
        self.bookmarks = list(bookmarks)
        self.update()


    def set_timeline(self, timeline):
        self._marking = False
        self.timeline = timeline
        self.live_mono = None
        self.sel_a = self.sel_b = None
        self.playhead = 0.0
        self._peaks_key = None
        self.zoom_fit()
        self.selectionChanged.emit()


    def set_fade_ms(self, value):
        self.fade_ms = float(value)
        self.update()


    def set_end_fade(self, seconds):
        self.end_fade_s = float(seconds)
        self.update()


    def set_live(self, mono, label="", marks=None, env=None):
        self.live_mono = mono
        self.live_label = label
        self.live_marks = list(marks or [])
        self.live_env = env
        self.update()


    def clear_live(self):
        self.live_mono = None
        self.live_marks = []
        self.live_env = None
        self.update()


    def duration(self):
        return self.timeline.duration() if self.timeline else 0.0


    # ---- peak cache / painting ----------------------------------------------


    # Fetch the pixel envelope from the pyramid, cached per view/size
    def ensure_peaks(self, width):
        store = self.timeline.store if self.timeline else None
        if store is None:
            self.peaks = None
            return
        key = (width, round(self.view_start, 5), round(self.view_end, 5),
               store.frames())
        if key == self._peaks_key:
            return
        samplerate = store.samplerate
        self.peaks = store.peaks(self.view_start * samplerate,
                                 self.view_end * samplerate, width)
        self._peaks_key = key


    def paintEvent(self, event):
        canvas = QPainter(self)
        try:
            paint(self, canvas)
        finally:
            canvas.end()