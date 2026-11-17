"""
waveform/zoom.py - ZoomMixin: the visible time window and time <-> pixel maths.

Mixed into WaveformView. Needs: view_start, view_end, duration(), width(),
playhead, selection(), viewChanged, update().
"""

from .metrics import MIN_SPAN


class ZoomMixin:

    def span(self):
        return max(MIN_SPAN, self.view_end - self.view_start)


    # Set the window (clamped to the clip), drop the peak cache and repaint
    def _commit_view(self, start, span):
        total = max(MIN_SPAN, self.duration())
        span = min(total, max(MIN_SPAN, span))
        start = max(0.0, min(start, total - span))
        self.view_start, self.view_end = start, start + span
        self._peaks_cache_key = None
        self.viewChanged.emit()
        self.update()


    def zoom_fit(self):
        self._commit_view(0.0, max(MIN_SPAN, self.duration()))


    def zoom_selection(self):
        selected = self.selection()
        if not selected:
            return
        pad = max(0.02, (selected[1] - selected[0]) * 0.1)
        self._commit_view(selected[0] - pad, (selected[1] - selected[0]) + pad * 2)


    # Zoom by `factor` keeping the time under `focus` where it is on screen
    def zoom_at(self, focus, factor):
        if self.duration() <= 0:
            return
        span = self.span()
        fraction = (focus - self.view_start) / span if span > 0 else 0.5
        fraction = min(max(fraction, 0.0), 1.0)
        new_span = min(max(span * factor, MIN_SPAN), max(MIN_SPAN, self.duration()))
        self._commit_view(focus - fraction * new_span, new_span)


    # Playhead if visible, otherwise the middle of the window
    def zoom_anchor(self):
        if self.view_start <= self.playhead <= self.view_end:
            return self.playhead
        return self.view_start + self.span() / 2.0


    def zoom_in(self):
        self.zoom_at(self.zoom_anchor(), 0.5)


    def zoom_out(self):
        self.zoom_at(self.zoom_anchor(), 2.0)


    def scroll_to(self, start):
        self._commit_view(start, self.span())


    def centre_on(self, seconds):
        self._commit_view(seconds - self.span() / 2.0, self.span())


    # seconds -> widget x
    def time_to_x(self, seconds):
        return (seconds - self.view_start) / self.span() * self.width()


    # widget x -> seconds
    def x_to_time(self, x):
        return self.view_start + (x / max(1, self.width())) * self.span()


    # Keep a time inside the clip
    def clamp(self, seconds):
        return min(max(0.0, seconds), self.duration())