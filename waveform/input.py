"""
waveform/input.py - InputMixin: mouse, wheel, keyboard and context menu.

Mixed into WaveformView.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu

from .metrics import EDGE_PX, RULER_H


class InputMixin:

    def mousePressEvent(self, event):
        if self.duration() <= 0 or self.live_mono is not None:
            return
        x, y = event.position().x(), event.position().y()
        if event.button() == Qt.MiddleButton:
            self._pan_origin = (x, self.view_start)
            return
        if event.button() != Qt.LeftButton:
            return
        if y < RULER_H:
            self._drag_mode = "playhead"
            self.set_playhead(self.x_to_time(x))
            self.playheadMoved.emit(self.playhead)
            return
        current = self.selection()
        if current:
            if abs(x - self.time_to_x(current[0])) <= EDGE_PX:
                self.sel_first, self.sel_second = current[1], current[0]
                self._drag_mode = "edge"
                return
            if abs(x - self.time_to_x(current[1])) <= EDGE_PX:
                self.sel_first, self.sel_second = current[0], current[1]
                self._drag_mode = "edge"
                return
        if self._awaiting_mark_pair:
            self._drag_mode = "pending"           
            self._press_x = x
            self.set_playhead(self.clamp(self.x_to_time(x)))
            self.playheadMoved.emit(self.playhead)
            return
        self.sel_first = self.sel_second = self.clamp(self.x_to_time(x))
        self._drag_mode = "edge"
        self.set_playhead(self.sel_first)
        self.playheadMoved.emit(self.playhead)
        self.selectionChanged.emit()


    def mouseMoveEvent(self, event):
        x, y = event.position().x(), event.position().y()
        if self._pan_origin is not None:
            press_x, start_view = self._pan_origin
            shift = (press_x - x) / max(1, self.width()) * self.span()
            self._commit_view(start_view + shift, self.span())
            return
        if self._drag_mode == "playhead":
            self.set_playhead(self.x_to_time(x))
            self.playheadMoved.emit(self.playhead)
            return
        if self._drag_mode == "pending":
            if abs(x - self._press_x) < 3:
                return
            self._awaiting_mark_pair = False            # a drag makes a fresh selection
            self.sel_first = self.clamp(self.x_to_time(self._press_x))
            self.sel_second = self.clamp(self.x_to_time(x))
            self._drag_mode = "edge"
            self.selectionChanged.emit()
            self.update()
            return
        if self._drag_mode == "edge":
            self.sel_second = self.clamp(self.x_to_time(x))
            self.selectionChanged.emit()
            self.update()
            return
        current = self.selection()
        near_edge = current and (abs(x - self.time_to_x(current[0])) <= EDGE_PX or
                                 abs(x - self.time_to_x (current[1])) <= EDGE_PX)
        if y < RULER_H:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.SizeHorCursor if near_edge else Qt.IBeamCursor)


    def mouseReleaseEvent(self, event):
        if self._drag_mode == "edge" and self.selection() is None:
            self.sel_first = self.sel_second = None
            self.selectionChanged.emit()
        self._drag_mode = None
        self._pan_origin = None
        self.update()


    # Select the block under the cursor: a kept piece or a deleted gap
    def mouseDoubleClickEvent(self, event):
        if (self.duration() <= 0 or self.live_mono is not None
                or event.button() != Qt.LeftButton or not self.timeline):
            return
        x, y = event.position().x(), event.position().y()
        if y < RULER_H:
            return
        block = self.timeline.block_at(self.x_to_time(x))
        if block is None:
            return
        block_start, block_end, piece_index = block
        self.set_selection(block_start, block_end)
        self.blockSelected.emit(-1 if piece_index is None else piece_index)


    def wheelEvent(self, event):
        if self.duration() <= 0:
            return
        delta = event.angleDelta().y()
        if event.modifiers() & Qt.ShiftModifier:
            self._commit_view(self.view_start - delta / 120.0 * self.span() * 0.15,
                              self.span())
        else:
            self.zoom_at(self.x_to_time(event.position().x()), 0.8 if delta > 0 else 1.25)


    def keyPressEvent(self, event):
        if self.duration() <= 0:
            super().keyPressEvent(event)
            return
        key = event.key()
        if key == Qt.Key_Home:
            self.goto(0.0)
        elif key == Qt.Key_End:
            self.goto(self.duration())
        elif key == Qt.Key_PageUp:
            self._commit_view(self.view_start - self.span() * 0.9, self.span())
        elif key == Qt.Key_PageDown:
            self._commit_view(self.view_start + self.span() * 0.9, self.span())
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom_in()
        elif key == Qt.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)


    def contextMenuEvent(self, event):
        if not self.context_actions:
            return
        self.context_time = self.clamp(self.x_to_time(event.pos().x()))
        menu = QMenu(self)
        for action in self.context_actions:
            if action is None:
                menu.addSeparator()
            else:
                menu.addAction(action)
        menu.exec(event.globalPos())
        self.context_time = None


    # True while the user is dragging the playhead on the ruler
    def is_scrubbing(self):
        return self._drag_mode == "playhead"