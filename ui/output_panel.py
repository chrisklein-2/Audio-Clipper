"""
output_panel.py - OutputPanelMixin: the editing panel at the bottom of the main window (not available during recording), 
                                    with fades, threshold, ceiling, cover, and export buttons.
"""

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QGroupBox, QHBoxLayout, QLabel,
    QPushButton,  QSizePolicy, QVBoxLayout,
)
from .widgets import abtn, sep

from processing import BITRATES


class OutputPanelMixin:

    def _build_output_group(self):
        g = QGroupBox("OUTPUT  /  SLEEP-SAFE")
        g.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # sets the ms of fade in/out for each kept piece
        self.cut_fade = QDoubleSpinBox()
        self.cut_fade.setRange(0.0, 5000.0)
        self.cut_fade.setValue(500.0)
        self.cut_fade.setSingleStep(50.0)
        self.cut_fade.setSuffix(" ms")
        self.cut_fade.setMinimumWidth(95)
        self.cut_fade.setToolTip(
            "Every kept piece fades in at its start and out at\n"
            "its end. 500 ms = half a second each way.\n"
            "The orange wedges on the waveform show it."
        )
        self.cut_fade.valueChanged.connect(self.on_fade_changed)

        # sets the extra fade at the very end of the clip
        self.fade_out = QDoubleSpinBox()
        self.fade_out.setRange(0.0, 60.0)
        self.fade_out.setValue(0.0)
        self.fade_out.setSuffix(" s")
        self.fade_out.setMinimumWidth(80)
        self.fade_out.setToolTip("Extra long fade on the very end of the clip.")
        self.fade_out.valueChanged.connect(self.on_end_fade_changed)

        # "Quiet down loud parts" checkbox
        self.night_box = QCheckBox("Quiet down loud parts")
        self.night_box.setChecked(True)
        self.night_box.setToolTip("Compressor + ceiling. Only turns things DOWN.")
        self.night_box.toggled.connect(self.invalidate)

        # set the threshold of the recording
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(-40.0, -6.0)
        self.threshold.setValue(-20.0)
        self.threshold.setSuffix(" dB")
        self.threshold.setMinimumWidth(85)
        self.threshold.setToolTip(
            "Audio above this gets compressed.\n-20 gentle, -28 aggressive."
        )
        self.threshold.valueChanged.connect(self.invalidate)

        # set the ceiling of the recording
        self.ceiling = QDoubleSpinBox()
        self.ceiling.setRange(-24.0, -0.5)
        self.ceiling.setValue(-3.0)
        self.ceiling.setSuffix(" dB")
        self.ceiling.setMinimumWidth(85)
        self.ceiling.setToolTip("Peak ceiling. Nothing in the file exceeds this.")
        self.ceiling.valueChanged.connect(self.invalidate)

        # button to test threshold/ceiling settings
        self.test_btn = QPushButton("Test")
        self.test_btn.setObjectName("tiny")
        self.test_btn.setFixedWidth(44)
        self.test_btn.setToolTip("Play a 1 s tone at the ceiling level —\n"
                                 "the loudest the export is allowed to get.")
        self.test_btn.clicked.connect(self.test_ceiling)

        # sets the bitrate of the export file (32 kbps, 48 kbps, 64 kbps...)
        self.bitrate = QComboBox()
        for kbps, label in BITRATES:
            self.bitrate.addItem(label, kbps)
        self.bitrate.setCurrentIndex(1)
        self.bitrate.setToolTip("AAC / MP3 bitrate. 48 kbps is plenty for speech.")
        self.bitrate.currentIndexChanged.connect(self.update_status)

        # button that adds the cover image to the export
        self.cover_btn = QPushButton("Cover: none")
        self.cover_btn.setMinimumWidth(150)
        self.cover_btn.setToolTip("Artwork embedded into .m4a and .mp3 exports.")
        self.cover_btn.clicked.connect(self.choose_cover)

        # small 'x' next to cover button to clear it
        self.cover_clear = QPushButton("\u00d7")
        self.cover_clear.setObjectName("tiny")
        self.cover_clear.setFixedWidth(26)
        self.cover_clear.setToolTip("Remove the cover image")
        self.cover_clear.clicked.connect(lambda: self.set_cover(None))

        # play/play from start buttons
        self.play_btn = abtn(self.act_play, primary=True, min_w=115)
        self.start_btn = abtn(self.act_from_start, min_w=90)

        # play raw button
        self.raw_btn = QPushButton("Play raw")
        self.raw_btn.setToolTip("Play the original recording, ignoring the cuts.")
        self.raw_btn.clicked.connect(self.play_raw)

        # export/finalize buttons
        self.export_btn = abtn(self.act_export, primary=True, min_w=85)
        self.finalize_btn = abtn(self.act_finalize, primary=True, min_w=100)  

        # laying out the top
        top = QHBoxLayout()
        top.setSpacing(7)
        top.addWidget(QLabel("Fade per cut"))
        top.addWidget(self.cut_fade)
        top.addWidget(QLabel("End fade"))
        top.addWidget(self.fade_out)
        top.addWidget(sep())
        top.addWidget(self.night_box)
        top.addWidget(QLabel("Threshold"))
        top.addWidget(self.threshold)
        top.addWidget(QLabel("Ceiling"))
        top.addWidget(self.ceiling)
        top.addWidget(self.test_btn)
        top.addStretch(1)

        # laying out the bottom
        bottom = QHBoxLayout()
        bottom.setSpacing(7)
        bottom.addWidget(self.play_btn)
        bottom.addWidget(self.start_btn)
        bottom.addWidget(self.raw_btn)
        bottom.addWidget(sep())
        bottom.addWidget(self.bitrate)
        bottom.addWidget(self.cover_btn)
        bottom.addWidget(self.cover_clear)
        bottom.addStretch(1)
        bottom.addWidget(self.export_btn)
        bottom.addWidget(self.finalize_btn) 

        # group the box (top + bottom)
        outer = QVBoxLayout(g)
        outer.setSpacing(7)
        outer.addLayout(top)
        outer.addLayout(bottom)
        return g