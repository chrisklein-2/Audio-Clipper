"""
waveform/fade_painter.py - draws the fade wedges on the waveform body.
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF

from editor.fades import cap_fades
from theme import COL_FADE

from .metrics import FILL_MIN_PX, FULL_WEDGE_PX, MIN_WEDGE_PX



# One wedge: the part of the waveform body that the gain ramp takes away,
# between x_a (gain gain_a) and x_b (gain gain_b), both 0..1. The line gets
# thinner as the wedge shrinks, and the translucent fill disappears below
# FILL_MIN_PX.
def _lost_area(canvas, x_a, gain_a, x_b, gain_b, centre_y, top, bottom):
    size = abs(x_b - x_a)
    thickness = min(1.0, max(0.0, (size - MIN_WEDGE_PX) / (FULL_WEDGE_PX - MIN_WEDGE_PX)))
    pen_width = 1.0 + thickness
    fill = None
    if size >= FILL_MIN_PX:
        fill = QColor(COL_FADE)
        fill.setAlpha(50)
    for edge in (top, bottom):
        y_a = centre_y + (edge - centre_y) * gain_a
        y_b = centre_y + (edge - centre_y) * gain_b
        if fill is not None:
            polygon = QPolygonF([QPointF(x_a, y_a), QPointF(x_a, edge),
                                 QPointF(x_b, edge), QPointF(x_b, y_b)])
            canvas.setPen(Qt.NoPen)
            canvas.setBrush(QBrush(fill))
            canvas.drawPolygon(polygon)
            canvas.setBrush(Qt.NoBrush)
        canvas.setPen(QPen(COL_FADE, pen_width))
        canvas.drawLine(QPointF(x_a, y_a), QPointF(x_b, y_b))



# Draw the fade in / fade out of every kept piece, plus the end fade.
# The last piece shows ONE out-wedge: whichever of its own fade and the
# end fade is longer, because that is what the audio does.
def paint_fades(view, canvas, centre_y, scale):
    timeline = view.timeline
    if not timeline or not timeline.keeps or view.span() <= 0:
        return
    px_per_s = view.width() / view.span()
    default_fade_s = view.fade_ms / 1000.0
    top, bottom = centre_y - scale, centre_y + scale
    keeps = timeline.keeps
    last = len(keeps) - 1
    end_fade_s = min(getattr(view, "end_fade_s", 0.0), timeline.kept_duration())


    end_wins = False
    for i, keep in enumerate(keeps):
        x_start, x_end = view.time_to_x(keep.start), view.time_to_x(keep.end)
        fade_in_s, fade_out_s = timeline.effective_fades(keep, default_fade_s)
        fade_in_s, fade_out_s = cap_fades(fade_in_s, fade_out_s, keep.length())
        if i == last and end_fade_s > fade_out_s:
            end_wins = True
            fade_out_s = 0.0
        if x_end < -20 or x_start > view.width() + 20:
            continue
        half = (x_end - x_start) / 2.0
        if fade_in_s > 0:
            wedge_px = min(max(fade_in_s * px_per_s, MIN_WEDGE_PX), half)
            if wedge_px >= 1.0:
                _lost_area(canvas, x_start, 0.0, x_start + wedge_px, 1.0,
                           centre_y, top, bottom)
        if fade_out_s > 0:
            wedge_px = min(max(fade_out_s * px_per_s, MIN_WEDGE_PX), half)
            if wedge_px >= 1.0:
                _lost_area(canvas, x_end - wedge_px, 1.0, x_end, 0.0,
                           centre_y, top, bottom)


    if not end_wins or end_fade_s <= 0:
        return
    if end_fade_s * px_per_s < MIN_WEDGE_PX:
        x_end = view.time_to_x(keeps[-1].end)
        piece_px = x_end - view.time_to_x(keeps[-1].start)
        x_start = x_end - min(MIN_WEDGE_PX, max(1.0, piece_px))
        _lost_area(canvas, x_start, 1.0, x_end, 0.0, centre_y, top, bottom)
        return
    covered_s = 0.0                      # output seconds already covered
    for keep in reversed(keeps):
        if covered_s >= end_fade_s:
            break
        use = min(end_fade_s - covered_s, keep.length())
        gain_end, gain_start = covered_s / end_fade_s, (covered_s + use) / end_fade_s
        x_end, x_start = view.time_to_x(keep.end), view.time_to_x(keep.end - use)
        _lost_area(canvas, x_start, gain_start, x_end, gain_end, centre_y, top, bottom)
        covered_s += use