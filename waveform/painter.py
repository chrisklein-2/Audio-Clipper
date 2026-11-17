"""
waveform/painter.py - drawing for WaveformView: ruler, waveform, deleted zones,
selection, flags, bookmarks, playhead.

Fades are in fade_painter.py and the live recording view in live_painter.py.
Every function takes the view and a QPainter (called `canvas`). Painting reads
the view's state but never changes it, except asking the view to refresh its
peak cache, so this file stays a pure consumer of the view.
"""

import numpy as np
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QPen, QPolygonF

from editor import format_time
from theme import (COL_BG, COL_DEL_BG, COL_MARK, COL_PLAYHEAD, COL_RULER,
                   COL_RULER_LINE, COL_SEL, COL_SEL_EDGE, COL_TEXT,
                   COL_WAVE_DEL, COL_WAVE_KEEP, COL_WAVE_KEEP_SOFT)

from .metrics import RULER_H, NICE_STEPS      
from .fade_painter import paint_fades
from .live_painter import paint_live



# Pick a readable tick interval for the ruler at this zoom.
def pick_tick_step(span, width):
    target = max(1, width // 95)
    for step in NICE_STEPS:
        if span / step <= target:
            return step
    return NICE_STEPS[-1]



# Boolean mask: which pixel columns are inside kept audio.
def keep_mask(view, width):
    mask = np.zeros(width, dtype=bool)
    if not view.timeline:
        return mask
    for keep in view.timeline.keeps:
        x_start = int(np.floor(view.t2x(keep.start)))
        x_end = int(np.ceil(view.t2x(keep.end)))
        mask[max(0, x_start):min(width, max(0, x_end))] = True
    return mask



# Paint everything: ruler, waveform, deleted zones, fades, selection,
# markers, playhead. Called from WaveformView.paintEvent.
def paint(view, canvas):
    width, height = view.width(), view.height()
    body_top, body_height = RULER_H, height - RULER_H
    centre_y = body_top + body_height / 2.0
    canvas.fillRect(view.rect(), COL_BG)
    canvas.fillRect(0, 0, width, RULER_H, COL_RULER)
    canvas.setPen(QPen(COL_RULER_LINE, 1))
    canvas.drawLine(0, RULER_H - 1, width, RULER_H - 1)


    if view.live_mono is not None:
        paint_live(view, canvas, width, body_top, body_height, centre_y)
        return
    if not view.timeline or view.duration() <= 0:
        canvas.setPen(COL_TEXT)
        canvas.drawText(view.rect(), Qt.AlignCenter,
                        "Press Record and play something,\n"
                        "load an audio file, or drop one here.    (F1 = help)")
        return


    view.ensure_peaks(width)
    for start, end in view.timeline.deleted_ranges():
        x_start, x_end = view.t2x(start), view.t2x(end)
        canvas.fillRect(QRectF(x_start, body_top, max(1.0, x_end - x_start), body_height),
                        COL_DEL_BG)


    scale = body_height / 2.0 - 6
    if view.peaks is not None:
        mins, maxs = view.peaks
        mask = keep_mask(view, width)
        keep_pen, deleted_pen = QPen(COL_WAVE_KEEP, 1), QPen(COL_WAVE_DEL, 1)
        for x in range(width):
            canvas.setPen(keep_pen if mask[x] else deleted_pen)
            canvas.drawLine(x, int(centre_y - maxs[x] * scale),
                            x, int(centre_y - mins[x] * scale))
        canvas.setPen(QPen(COL_WAVE_KEEP_SOFT, 1))
        for keep in view.timeline.keeps:
            canvas.drawLine(int(view.t2x(keep.start)), int(centre_y),
                            int(view.t2x(keep.end)), int(centre_y))
    canvas.setPen(QPen(COL_WAVE_DEL, 1, Qt.DashLine))
    for start, end in view.timeline.deleted_ranges():
        canvas.drawLine(int(view.t2x(start)), int(centre_y),
                        int(view.t2x(end)), int(centre_y))


    paint_fades(view, canvas, centre_y, scale)
    _paint_selection(view, canvas, body_top, height)
    _paint_ruler(view, canvas, width)
    _paint_bookmarks(view, canvas)
    playhead_x = view.t2x(view.playhead)
    canvas.setPen(QPen(COL_PLAYHEAD, 1))
    canvas.drawLine(int(playhead_x), 0, int(playhead_x), height)



# Shade the selection and flag its two marker edges.
def _paint_selection(view, canvas, body_top, height):
    selected = view.selection()
    if selected:
        x_start, x_end = view.t2x(selected[0]), view.t2x(selected[1])
        canvas.fillRect(QRectF(x_start, body_top, x_end - x_start, height - body_top),
                        QBrush(COL_SEL))
        canvas.setPen(QPen(COL_SEL_EDGE, 2))
        canvas.drawLine(int(x_start), body_top, int(x_start), height)
        canvas.drawLine(int(x_end), body_top, int(x_end), height)
        canvas.setPen(COL_SEL_EDGE)
        canvas.drawText(int(min(x_start, x_end)) + 6, body_top + 32,
                        f"{format_time(selected[1] - selected[0])} selected")
    if view.sel_a is not None and view.sel_b is not None:
        low, high = sorted((view.sel_a, view.sel_b))
        flags = [(low, "[", False), (high, "]", True)]
    else:
        flags = []
        if view.sel_a is not None:
            flags.append((view.sel_a, "[", False))
        if view.sel_b is not None:
            flags.append((view.sel_b, "]", True))
    for value, label, on_right in flags:
        _paint_flag(view, canvas, view.t2x(value), body_top, label, on_right)



# Draw one marker flag: a small tag hanging off the top of the body.
def _paint_flag(view, canvas, x, body_top, label, on_right):
    flag_w, flag_h = 13.0, 15.0
    sign = -1.0 if on_right else 1.0
    polygon = QPolygonF([QPointF(x, body_top), QPointF(x + sign * flag_w, body_top),
                         QPointF(x + sign * flag_w, body_top + flag_h - 5),
                         QPointF(x, body_top + flag_h)])
    canvas.setPen(Qt.NoPen)
    canvas.setBrush(QBrush(COL_MARK))
    canvas.drawPolygon(polygon)
    canvas.setPen(QPen(COL_MARK, 1))
    canvas.drawLine(int(x), body_top, int(x), view.height())
    font = QFont(canvas.font())
    font.setBold(True)
    font.setPointSize(8)
    canvas.setFont(font)
    canvas.setPen(QColor("#1a1400"))
    canvas.drawText(QRectF(x + (0 if not on_right else -flag_w), body_top,
                           flag_w, flag_h - 3),
                    Qt.AlignCenter, label)



# Draw ruler tick marks and time labels.
def _paint_ruler(view, canvas, width):
    step = pick_tick_step(view.span(), width)
    font = QFont(canvas.font())
    font.setPointSize(8)
    font.setBold(False)
    canvas.setFont(font)
    canvas.setPen(COL_TEXT)
    tick_time = np.ceil(view.view_start / step) * step
    while tick_time <= view.view_end:
        x = int(view.t2x(tick_time))
        canvas.drawLine(x, RULER_H - 6, x, RULER_H - 1)
        canvas.drawText(x + 3, RULER_H - 8, format_time(tick_time))
        tick_time += step



# Small yellow dots on the ruler for bookmarked spots.
def _paint_bookmarks(view, canvas):
    if not view.bookmarks:
        return
    canvas.setPen(QPen(COL_MARK, 1))
    canvas.setBrush(QBrush(COL_MARK))
    radius = 3
    dot_y = RULER_H - radius - 2
    for bookmark_time in view.bookmarks:
        x = int(view.t2x(bookmark_time))
        if -radius <= x <= view.width() + radius:
            canvas.drawEllipse(x - radius, dot_y - radius, radius * 2, radius * 2)
            canvas.drawLine(x, RULER_H, x, RULER_H + 8)
    canvas.setBrush(Qt.NoBrush)