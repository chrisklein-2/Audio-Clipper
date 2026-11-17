"""
waveform/metrics.py - sizes and constants shared by the waveform files.
"""

RULER_H = 22          # height of the time ruler, pixels
EDGE_PX = 6           # how close the mouse must be to grab a selection edge
MIN_SPAN = 0.02       # smallest zoom window, seconds

MIN_WEDGE_PX = 4.0    # narrowest a fade is drawn, so it shows fully zoomed out
FILL_MIN_PX = 14.0    # narrower than this, the translucent fill is dropped
FULL_WEDGE_PX = 24.0  # this wide or wider, the lines are full thickness

NICE_STEPS = [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600,
              1800, 3600]