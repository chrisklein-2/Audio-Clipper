"""controllers/bookmarks.py - BookmarksMixin."""

from editor import format_time


class BookmarksMixin:

    def add_bookmark(self):
        """Drop a marker at the recording time, or at the playhead when editing."""
        if self.recorder is not None:
            t = self.recorder.elapsed()
        elif self.timeline.duration() > 0:
            ctx = self.wave.context_time
            t = self.wave.playhead if ctx is None else ctx
        else:
            return
        self.bookmarks.append(t)
        self.bookmarks.sort()
        self.wave.set_bookmarks(self.bookmarks)
        self.update_actions()
        self.statusBar().showMessage(f"Bookmark at {format_time(t)}", 3000)

    def remove_nearest_bookmark(self):
        """Remove the bookmark closest to the right-click (or the playhead)."""
        if not self.bookmarks or self.timeline.duration() <= 0:
            return
        ctx = self.wave.context_time
        t = self.wave.playhead if ctx is None else ctx
        nearest = min(self.bookmarks, key=lambda b: abs(b - t))
        if abs(nearest - t) < max(2.0, self.wave.span() * 0.02):
            self.bookmarks.remove(nearest)
            self.wave.set_bookmarks(self.bookmarks)
            self.update_actions()
            self.statusBar().showMessage(
                f"Removed bookmark at {format_time(nearest)}", 3000)
        else:
            self.statusBar().showMessage("No bookmark near here", 3000)

    def clear_bookmarks(self):
        self.bookmarks.clear()
        self.wave.set_bookmarks(self.bookmarks)
        self.update_actions()
        self.statusBar().showMessage("All bookmarks cleared", 3000)

    def goto_prev_bookmark(self):
        if not self.bookmarks:
            return
        before = [b for b in self.bookmarks if b < self.wave.playhead - 0.05]
        if before:
            self.wave.goto(before[-1])

    def goto_next_bookmark(self):
        if not self.bookmarks:
            return
        after = [b for b in self.bookmarks if b > self.wave.playhead + 0.05]
        if after:
            self.wave.goto(after[0])