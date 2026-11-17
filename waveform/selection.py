"""
waveform/selection.py - SelectionMixin: selection, in/out marks and playhead.

Mixed into WaveformView. sel_a / sel_b are the two ends in the order they were
set (not sorted); selection() returns them sorted, or None if too small.
"""


class SelectionMixin:

    def selection(self):
        if self.sel_a is None or self.sel_b is None:
            return None
        start, end = sorted((self.sel_a, self.sel_b))
        return None if end - start < 0.005 else (start, end)


    def clear_selection(self):
        self._marking = False
        self.sel_a = self.sel_b = None
        self.selectionChanged.emit()
        self.update()


    def select_all(self):
        self._marking = False
        if self.duration() > 0:
            self.sel_a, self.sel_b = 0.0, self.duration()
            self.selectionChanged.emit()
            self.update()


    def set_selection(self, start, end):
        self._marking = False
        self.sel_a, self.sel_b = self.clamp(start), self.clamp(end)
        self.selectionChanged.emit()
        self.update()


    # Time used by the mark actions: the right-click spot, else the playhead
    def _mark_time(self):
        return self.playhead if self.context_time is None else self.context_time


    def mark_in(self):
        if self.duration() <= 0:
            return
        mark_time = self._mark_time()
        if self._marking and self.sel_a is None and self.sel_b is not None:
            self.sel_a = mark_time                     # completes a mark-out-first pair
            self._marking = False
        else:
            self.sel_a, self.sel_b = mark_time, None   # start a new pair, wait for out
            self._marking = True
        self.selectionChanged.emit()
        self.update()


    def mark_out(self):
        if self.duration() <= 0:
            return
        mark_time = self._mark_time()
        if self._marking and self.sel_b is None and self.sel_a is not None:
            self.sel_b = mark_time                     # completes the pair
            self._marking = False
        else:
            self.sel_a, self.sel_b = None, mark_time   # start a new pair, wait for in
            self._marking = True
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