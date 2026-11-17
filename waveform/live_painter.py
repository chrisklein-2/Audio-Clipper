"""
waveform/live_painter.py - the live view drawn while recording.
"""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen

from theme import COL_MARK, COL_TEXT_BRIGHT

from .metrics import RULER_H



# Per-pixel min/max envelope of a flat mono array (live view only).
def live_peaks(mono, width):
    if width < 1 or len(mono) < 2:
        return None
    edges = np.linspace(0, len(mono), width + 1).astype(np.int64)
    mins = np.zeros(width, dtype=np.float32)
    maxs = np.zeros(width, dtype=np.float32)
    for i in range(width):
        first, last = edges[i], max(edges[i] + 1, edges[i + 1])
        chunk = mono[first:min(last, len(mono))]
        if chunk.size:
            mins[i], maxs[i] = chunk.min(), chunk.max()
    return mins, maxs



# Per-pixel min/max from a bucket overview (the whole-recording live view).
def env_peaks(mins, maxs, width):
    count = len(mins)
    if width < 1 or count < 1:
        return None
    if count <= width:
        index = (np.arange(width) * count / float(width)).astype(np.int64)
        return mins[index], maxs[index]
    starts = np.linspace(0, count, width + 1).astype(np.int64)[:-1]
    return np.minimum.reduceat(mins, starts), np.maximum.reduceat(maxs, starts)



# Draw the live view while recording, with bookmark markers.
def paint_live(view, canvas, width, body_top, body_height, centre_y):
    if view.live_env is not None:
        peaks = env_peaks(view.live_env[0], view.live_env[1], width)
    else:
        peaks = live_peaks(view.live_mono, width)
    if peaks is not None:
        mins, maxs = peaks
        scale = body_height / 2.0 - 6
        canvas.setPen(QPen(QColor("#e05c5c"), 1))
        for x in range(width):
            canvas.drawLine(x, int(centre_y - maxs[x] * scale),
                            x, int(centre_y - mins[x] * scale))
    if view.live_marks:
        radius = 3
        dot_y = RULER_H - radius - 2
        canvas.setPen(QPen(COL_MARK, 1))
        canvas.setBrush(QBrush(COL_MARK))
        for fraction in view.live_marks:
            x = int(fraction * width)
            canvas.drawEllipse(x - radius, dot_y - radius, radius * 2, radius * 2)
            canvas.drawLine(x, RULER_H, x, view.height())
        canvas.setBrush(Qt.NoBrush)
    canvas.setPen(COL_TEXT_BRIGHT)
    canvas.drawText(10, RULER_H - 7, view.live_label)