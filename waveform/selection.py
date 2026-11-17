"""
waveform/selection.py - SelectionMixin: selection, in/out marks and playhead.

Mixed into WaveformView. sel_first / sel_second are the two ends in the order they were
set (not sorted); selection() returns them sorted, or None if too small.
"""


class SelectionMixin:

    def selection(self):
        if self.sel_first is None or self.sel_second is None:
            return None
        start, end = sorted((self.sel_first, self.sel_second))
        return None if end - start < 0.005 else (start, end)


    def clear_selection(self):
        self._awaiting_mark_pair = False
        self.sel_first = self.sel_second = None
        self.selectionChanged.emit()
        self.update()


    def select_all(self):
        self._awaiting_mark_pair = False
        if self.duration() > 0:
            self.sel_first, self.sel_second = 0.0, self.duration()
            self.selectionChanged.emit()
            self.update()


    def set_selection(self, start, end):
        self._awaiting_mark_pair = False
        self.sel_first, self.sel_second = self.clamp(start), self.clamp(end)
        self.selectionChanged.emit()
        self.update()


    # Time used by the mark actions: the right-click spot, else the playhead
    def _mark_time(self):
        return self.playhead if self.context_time is None else self.context_time


    def mark_in(self):
        if self.duration() <= 0:
            return
        mark_time = self._mark_time()
        if self._awaiting_mark_pair and self.sel_first is None and self.sel_second is not None:
            self.sel_first = mark_time                     # completes a mark-out-first pair
            self._awaiting_mark_pair = False
        else:
            self.sel_first, self.sel_second = mark_time, None   # start a new pair, wait for out
            self._awaiting_mark_pair = True
        self.selectionChanged.emit()
        self.update()


    def mark_out(self):
        if self.duration() <= 0:
            return
        mark_time = self._mark_time()
        if self._awaiting_mark_pair and self.sel_second is None and self.sel_first is not None:
            self.sel_second = mark_time                     # completes the pair
            self._awaiting_mark_pair = False
        else:
            self.sel_first, self.sel_second = None, mark_time   # start a new pair, wait for in
            self._awaiting_mark_pair = True
        self.selectionChanged.emit()
        self.update()


    def set_playhead(self, seconds):
        self.playhead = self.clamp(seconds)
        self.update()


    # Move the playhead, scroll it into view if needed, and tell the window
    def goto(self, seconds):
        self.set_playhead(seconds)
        if not (self.view_start <= self.playhead <= self.view_end):
            self.centre_on(self.playhead)
        self.playheadMoved.emit(self.playhead)